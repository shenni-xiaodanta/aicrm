"""采集任务业务层：建任务 → 后台线程执行 → 前端轮询进度。

线程模型沿用项目同步风格：start_crawl 校验 + 落一条 running 任务后
立即返回 task_id，实际抓取在 daemon 线程跑，不引入任务队列——
项目规模不需要 Celery/RQ，APScheduler 留到定时采集那期。

单站锁：落任务前查同站 running 任务（dao.running_task_for_site），
运行中的任务本期不提供取消接口，跑完自然结束。
"""
import hashlib
import logging
import threading
from datetime import datetime
from urllib.parse import urlsplit

from com.crm.common.db import tx
from com.crm.common.exceptions import BizException
from com.crm.crawl import dao
from com.crm.crawler.fetcher import FetchError, get as fetch
from com.crm.crawler.paginator import iter_pages
from com.crm.crawler.parser import extract_detail, parse_list
from com.crm.crawler.probe import ProbeError, run_probe
from com.crm.crawler.template import validate_template
from com.crm.helper.texthelper import clip
from com.crm.helper.urlhelper import has_path
from com.crm.shangji.service import extract_and_save

logger = logging.getLogger(__name__)

# 增量语义：从入口起自动翻页，连续 N 条命中已有 md5 即认为
# 「后面都是旧的」就停。第一次跑翻到 max_pages，之后每次
# 基本第 1 页翻两条就收工，省下整站重抓的时间与 LLM 调用。
DUP_STOP = 5


# ---------------------------------------------------------------------
# 供 API 调用的同步入口
# ---------------------------------------------------------------------
def list_regions():
    """地区采集点列表（含站点配方摘要），供前端下拉与站点管理页。"""
    return dao.list_regions()


def list_sites():
    return dao.list_sites()


def get_task(task_id):
    task = dao.get_task(task_id)
    if not task:
        raise BizException("采集任务不存在", code=1000)
    return task


def list_tasks(limit=50):
    return dao.list_tasks(limit)


def start_crawl(region_id, user_id):
    """发起一次地区采集：校验 → 落任务 → 起后台线程，立即返回。"""
    region = dao.get_region(region_id)
    if not region:
        raise BizException("采集地区不存在", code=1000)
    if not region["enabled"] or not region["s_enabled"]:
        raise BizException("该地区或所属站点已停用", code=1000)
    if region["s_render_mode"] != "http":
        raise BizException(
            f"该站点需要浏览器渲染（render_mode={region['s_render_mode']}），暂不支持",
            code=1000,
        )
    if dao.running_task_for_site(region["site_id"]):
        raise BizException("该站点已有采集任务在运行，请稍后再试", code=1000)

    task_id = dao.create_task(region_id, region["site_id"], user_id)
    threading.Thread(
        target=_run_task, args=(task_id,), daemon=True, name=f"crawl-task-{task_id}"
    ).start()
    logger.info(
        "采集任务 #%s 启动 %s/%s by user=%s",
        task_id, region["province"], region["city"], user_id,
    )
    return {"task_id": task_id}


def update_site(site_id, fields):
    """更新站点配方（后台高级配置区用）。只允许改这几个字段。

    选择器/翻页改动先与库中现有配方合并过 validate_template——
    人工改坏一个 key 就静默入库，下次采集才会炸，问题被推迟一整步。
    """
    allowed = ("selectors", "pagination", "charset", "render_mode",
               "request_interval", "max_retry", "max_pages", "enabled")
    patch = {k: v for k, v in (fields or {}).items() if k in allowed and v is not None}
    if not patch:
        raise BizException("没有可更新的字段", code=1000)
    site = dao.get_site(site_id)
    if not site:
        raise BizException("站点不存在", code=1000)
    try:
        validate_template({
            "selectors": patch.get("selectors") or site.get("selectors") or {},
            "pagination": patch.get("pagination") or site.get("pagination") or {},
        })
    except ValueError as e:
        raise BizException(f"站点配方不合法：{e}", code=1000)
    dao.update_site(site_id, patch)
    logger.info("站点配方更新 id=%s fields=%s", site_id, list(patch))
    return dao.get_site(site_id)


def probe_site(list_url, site_code=None, site_name=None, province=None, city=None):
    """LLM 探测站点结构并保存模板（POST /crawl/probe 的业务入口）。

    流程：下载入口页 → LLM 读骨架生成配方 → 真页面三重回验
    （列表 / 正文 / 翻页）→ 事务内新建或覆盖站点模板 → 按需登记地区。
    失败统一转 BizException 可读文案，绝不入库半成品模板；
    对已有 site_code 重探 = 覆盖配方（模板自愈 / 改版恢复都走这条）。
    """
    list_url = (list_url or "").strip()
    if not has_path(list_url):
        raise BizException(
            "list_url 必须是带路径的 http(s) 地址，例如 https://xxx.gov.cn/jyxx/002002/002002001/2.html",
            code=1000,
        )

    try:
        template, evidence = run_probe(list_url)
    except FetchError as e:
        raise BizException(f"探测失败：列表页下载失败（{clip(str(e), 150)}）", code=1000)
    except ProbeError as e:
        raise BizException(f"探测失败：{e}", code=1000)

    code = clip(site_code, 50) or _site_code_from_url(list_url)
    with tx():
        existing = dao.get_site_by_code(code)
        if existing:
            patch = {
                "selectors": template["selectors"],
                "pagination": template["pagination"],
                "charset": "",          # 探测无法可靠判定编码，交给 fetcher 自动猜
                "probed_at": datetime.now(),
            }
            if (site_name or "").strip():
                patch["site_name"] = clip(site_name, 100)
            dao.update_site(existing["id"], patch)
            site_id, created = existing["id"], False
        else:
            name = ((site_name or "").strip()
                    or template.get("site_name")
                    or code)
            site_id = dao.insert_site(
                code, clip(name, 100),
                template["selectors"], template["pagination"],
            )
            created = True

        # 省市都给了才登记地区采集点；只建模板不建地区是合法的
        #（站点管理页后续做增删改，那里再补地区）
        region_id = None
        if (province or "").strip() and (city or "").strip():
            region_id = dao.upsert_region(
                site_id, clip(province, 50), clip(city, 50), clip(list_url, 2048)
            )

    logger.info(
        "站点探测入库 code=%s created=%s site_id=%s region_id=%s items=%s",
        code, created, site_id, region_id, evidence["list_items"],
    )
    return {
        "site_id": site_id,
        "site_code": code,
        "created": created,
        "region_id": region_id,
        "template": template,
        "evidence": evidence,
    }


def _site_code_from_url(list_url):
    """从域名推导站点编码（未显式传 site_code 时用）：去 www、点换下划线。

    同一域名永远推出同一编码——对同一站点反复探测天然走「覆盖」分支，
    不会一探就插一条新模板。
    """
    host = urlsplit(list_url).netloc.split("@")[-1].split(":")[0].lower()
    if host.startswith("www."):
        host = host[4:]
    return clip(host.replace(".", "_"), 50)


# ---------------------------------------------------------------------
# 后台线程执行体
# ---------------------------------------------------------------------
def _run_task(task_id):
    """线程入口：包一层兜底，任何异常都要把任务标成 failed，
    不能让任务永远停在 running 状态把单站锁占死。"""
    try:
        _crawl(task_id)
    except Exception as e:  # noqa: BLE001 —— 兜底必须在最外层
        logger.exception("采集任务 #%s 异常终止", task_id)
        dao.update_task(task_id, {
            "status": "failed",
            "stop_reason": "error",
            "fail_detail": [{"url": "", "title": "", "reason": clip(str(e), 200)}],
            "finished_at": datetime.now(),
        })


def _crawl(task_id):
    """单次地区采集的主流程：翻页 → 解析 → 增量判断 → 抓详情 → 交
    shangji.extract_and_save 抽取入库。进度每页落一次库，前端轮询可见。"""
    task = dao.get_task(task_id)
    region = dao.get_region(task["region_id"])
    site = dao.get_site(region["site_id"])
    selectors = site["selectors"] or {}
    pagination = site["pagination"] or {}
    charset = (site.get("charset") or "").strip()
    max_retry = int(site.get("max_retry") or 2)
    max_pages = int(site.get("max_pages") or 10)
    interval = float(site.get("request_interval") or 3.0)

    # href 拼接 / 相对翻页模板补全的基准用完整入口页 URL：裸域名会把
    # 列表页自身目录丢掉，相对链接（202611/t...htm）会拼成 404 地址
    # （ccgp 实测踩坑，探测侧同修）
    list_url_full = region["list_url"]

    pages_crawled = 0
    total_items = new_count = dup_count = fail_count = 0
    fail_detail = []
    consecutive_dups = 0
    stop_reason = None
    status = "success"

    for page_url, page_no in iter_pages(pagination, list_url_full, max_pages):
        try:
            html = fetch(page_url, charset=charset, max_retry=max_retry)
        except FetchError as e:
            fail_detail.append({
                "url": page_url, "title": f"第 {page_no} 页列表页",
                "reason": clip(str(e), 200),
            })
            stop_reason = "error"
            break

        items = parse_list(html, selectors, list_url_full)
        total_items += len(items)

        if not items:
            # 翻过头了（或列表结构变化），这一页是空的——停，留痕可查
            fail_detail.append({
                "url": page_url, "title": f"第 {page_no} 页",
                "reason": "列表页解析出 0 条，停止翻页",
            })
            stop_reason = "empty_page"
            break

        page_candidates = []
        for item in items:
            md5 = hashlib.md5(item["url"].encode("utf-8")).hexdigest()
            if dao.lead_exists(md5):
                dup_count += 1
                consecutive_dups += 1
                if consecutive_dups >= DUP_STOP:
                    break  # 连续 5 条都是旧的，本页剩余大概率也是旧的
                continue
            consecutive_dups = 0

            try:
                # referer 带上列表页：部分政采站校验来源页，不带会被静默拦截
                detail_html = fetch(item["url"], charset=charset, max_retry=max_retry,
                                    referer=page_url)
            except FetchError as e:
                fail_count += 1
                fail_detail.append({
                    "url": item["url"], "title": item["title"],
                    "reason": clip(str(e), 200),
                })
                continue

            content = extract_detail(detail_html, selectors.get("detail_content"))
            if not content:
                fail_count += 1
                fail_detail.append({
                    "url": item["url"], "title": item["title"],
                    "reason": "详情页正文为空",
                })
                continue
            page_candidates.append({
                "title": item["title"], "date": item["date"],
                "url": item["url"], "content": content,
            })

        # 本页候选交给统一的抽取入库链路（LLM 批量并发 + 地理编码 + 去重插入）
        if page_candidates:
            result = extract_and_save(page_candidates)
            new_count += result["saved"]
            for row in result["failed_rows"]:
                fail_count += 1
                fail_detail.append(row)

        pages_crawled += 1
        # 进度落库：前端轮询看到的是逐页推进，不是黑盒转圈
        dao.update_task(task_id, {
            "pages_crawled": pages_crawled,
            "total_items": total_items,
            "new_count": new_count,
            "dup_count": dup_count,
            "fail_count": fail_count,
        })

        if consecutive_dups >= DUP_STOP:
            stop_reason = "no_new"
            break
        if pages_crawled >= max_pages:
            stop_reason = "max_pages"
            break

    # 终态判定：error 起步即挂 = failed；有失败/中途异常 = partial；其余 success
    if stop_reason == "error" and pages_crawled == 0:
        status = "failed"
    elif fail_count > 0 or stop_reason in ("error", "empty_page"):
        status = "partial"

    dao.update_task(task_id, {
        "status": status,
        "stop_reason": stop_reason or "max_pages",
        "pages_crawled": pages_crawled,
        "total_items": total_items,
        "new_count": new_count,
        "dup_count": dup_count,
        "fail_count": fail_count,
        "fail_detail": fail_detail or None,
        "finished_at": datetime.now(),
    })
    dao.touch_region(region["id"], task_id)
    logger.info(
        "采集任务 #%s 结束 status=%s stop=%s pages=%s new=%s dup=%s fail=%s",
        task_id, status, stop_reason, pages_crawled, new_count, dup_count, fail_count,
    )
