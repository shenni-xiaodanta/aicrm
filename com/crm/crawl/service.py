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
    """地区采集点列表（含站点摘要），采集任务下拉与站点管理页共用。

    可用性由后端一次性算好（页面不做布尔组合，沿用项目约定）：
      - 存在即可采：「停用」这层概念已取消，站点失效的唯一处理方式是删除；
      - 站点 render_mode 不是 http 的仍然拦住（浏览器渲染留到二期）。
    disabled_reason 给前端选文案，目前只有 render 一种原因。
    """
    rows = dao.list_regions()
    for row in rows:
        row["can_crawl"] = row["s_render_mode"] == "http"
        row["disabled_reason"] = "" if row["can_crawl"] else "render"
    # 能采的排在前面——不可选项不该挤在用户眼前；同组内按省市排
    rows.sort(key=lambda row: (
        not row["can_crawl"], row["province"] or "", row["city"] or ""
    ))
    return rows


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
        raise BizException("该采集地区不存在（可能已被删除）", code=1000)
    # 不再校验 enabled：停用概念已取消，站点失效就直接删；
    # 但浏览器渲染的站点本期确实采不了，这一条必须留
    if region["s_render_mode"] != "http":
        raise BizException(
            "该站点需要浏览器渲染，本期不支持（请换一个服务端渲染的列表页）",
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


def add_region(site_id, province, city, list_url=None):
    """给站点登记地区采集点（站点管理页用），不重跑模型。

    探测只负责生成解析配方；一个站点模板能挂 N 个地区（同构站点共用
    选择器），地区登记是独立动作——用户只需回答「用在哪个地区」，
    入口地址从站点配方的翻页模板自动反推，不让人手填（他本来也不该知道）。
    """
    province = (province or "").strip()
    city = (city or "").strip()
    list_url = (list_url or "").strip()
    if not province or not city:
        # 省市只填一个就静默不登记，是之前实测踩到的坑：管理员以为
        # 登记成功了，下拉里却始终只有旧地区——要么都填要么明确报错
        raise BizException("省份和城市都要填才能登记采集地区", code=1000)
    site = dao.get_site(site_id)
    if not site:
        raise BizException("站点不存在（可能已被删除）", code=1000)
    if not has_path(list_url):
        # 用户不该被要求知道入口地址：新增地区时用站点记录下的探测入口页
        list_url = (site.get("entry_url") or "").strip()
    if not has_path(list_url):
        raise BizException("该站点没有记录入口地址，请重新识别一次该站点", code=1000)
    region_id = dao.upsert_region(
        site_id, clip(province, 50), clip(city, 50), clip(list_url, 2048)
    )
    logger.info(
        "站点登记采集地区 site=%s region_id=%s %s/%s",
        site["site_code"], region_id, province, city,
    )
    return {
        "region_id": region_id,
        "site_code": site["site_code"],
        "site_name": site["site_name"],
    }


def delete_site(site_id):
    """删除站点（软删）：其下地区一并删除，历史任务保留可查。

    为什么软删不硬删：任务表靠 region_id / site_id JOIN 出省市和站点名，
    硬删会让历史任务那一行直接消失。is_deleted = id 让已删行不再可见，
    但 JOIN 仍能取到名称。
    为什么先拦运行中任务：后台线程正在读这套配方和地区行，删了会中途崩。
    """
    site = dao.get_site(site_id)
    if not site:
        raise BizException("站点不存在（可能已被删除）", code=1000)
    if dao.running_task_for_site(site_id):
        raise BizException("该站点有采集任务正在运行，等它结束再删", code=1000)
    region_count = dao.count_regions_of_site(site_id)
    with tx():
        dao.soft_delete_regions_of_site(site_id)
        dao.soft_delete_site(site_id)
    logger.info(
        "站点已删除 site=%s site_id=%s regions=%s",
        site["site_code"], site_id, region_count,
    )
    return {
        "site_id": site_id,
        "site_name": site["site_name"],
        "regions_removed": region_count,
    }


def delete_region(region_id):
    """删除单个地区采集点（软删）。已入库的商机不受影响。"""
    region = dao.get_region(region_id)
    if not region:
        raise BizException("采集地区不存在（可能已被删除）", code=1000)
    if dao.running_task_for_region(region_id):
        raise BizException("该地区有采集任务正在运行，等它结束再删", code=1000)
    dao.soft_delete_region(region_id)
    logger.info(
        "采集地区已删除 region_id=%s %s/%s",
        region_id, region["province"], region["city"],
    )
    return {
        "region_id": region_id,
        "province": region["province"],
        "city": region["city"],
    }


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
                # 记住这次探测的入口页：给已有站点「添加地区」时当默认入口，
                # 用户只填省市，不用再被告知网址
                "entry_url": clip(list_url, 2048),
                "probed_at": datetime.now(),
            }
            if (site_name or "").strip():
                patch["site_name"] = clip(site_name, 100)
            dao.update_site(existing["id"], patch)
            site_id, created = existing["id"], False
            stored_name = patch.get("site_name") or existing["site_name"]
        else:
            stored_name = ((site_name or "").strip()
                           or template.get("site_name")
                           or code)
            site_id = dao.insert_site(
                code, clip(stored_name, 100),
                template["selectors"], template["pagination"],
                entry_url=clip(list_url, 2048),
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
        "site_name": stored_name,
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
    site = dao.get_site(region["site_id"]) if region else None
    if not region or not site:
        # 删除接口已经拦了运行中任务，这里只是兜底：真被删了就带可读原因终止，
        # 不能让任务卡在 running 把单站锁占死
        raise RuntimeError("采集地区或站点已被删除，任务终止")
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
