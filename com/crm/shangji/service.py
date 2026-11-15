"""商机采集：爬取 -> LLM 批量抽取 -> 地理编码 -> 入库。"""
import hashlib
import logging

from com.crm.common.exceptions import BizException
from com.crm.common.llm import llm
from com.crm.helper.gishelper import resolve_coords
from com.crm.helper.htmlhelper import run_all_tender_crawl
from com.crm.helper.texthelper import clip, json_list
from com.crm.helper.urlhelper import is_origin, normalize_source, origin
from com.crm.shangji import dao
from com.crm.shangji.prompts import extract_prompt
from com.crm.shangji.schemas import LeadExtraction

logger = logging.getLogger(__name__)

# deepseek-flash 是思考模式，不支持强制 tool_choice，这里用 json_mode
extract_chain = extract_prompt | llm.with_structured_output(LeadExtraction, method="json_mode")

def extract_and_save(candidates):
    """对已抓好正文的公告列表执行 LLM 抽取 + 地理编码 + 去重入库。

    candidates: [{title, date, url, content}]（content 已按需截断）
    返回 {total, saved, failed, failed_rows}——failed_rows 是逐条失败
    明细 [{url, title, reason}]，供采集任务表落 fail_detail。

    拆出本函数的原因：旧链路 crawl_and_save 与新的任务式采集（crawl
    模块）共用同一套抽取入库逻辑，只有"怎么拿到公告"不同。
    注意：saved + failed 可能小于 total，重复 URL 会被 INSERT IGNORE
    静默跳过，这部分既不算 saved 也不算 failed。
    """
    inputs = [{
        "title": clip(row.get("title"), 500),
        "date": clip(row.get("date"), 50),
        "url": clip(row.get("url"), 2048),
        "content": (row.get("content") or "").strip()[:6000],
    } for row in candidates]

    # batch 保持输入顺序；return_exceptions=True 让单条失败以异常对象返回，
    # 后面的 zip(candidates, results) 才能一一对应。
    results = extract_chain.batch(
        inputs,
        config={"max_concurrency": 4},
        return_exceptions=True,
    )

    saved = failed = 0
    failed_rows = []
    for row, result in zip(candidates, results):
        if isinstance(result, Exception):
            failed += 1
            failed_rows.append({
                "url": row.get("url", ""),
                "title": row.get("title", ""),
                "reason": f"LLM 抽取失败：{clip(str(result), 180)}",
            })
            continue
        # 模型给出非零坐标就直接用；否则按地址 + 省市做高德地理编码
        lng, lat = resolve_coords(
            result.longitude, result.latitude, result.project_address,
            province=result.province, city=result.city,
        )
        # 每个字段按数据库列宽裁剪；needs/objections 序列化为 JSON 字符串
        record = {
            "customer": clip(result.customer, 200),
            "industry": clip(result.industry, 100),
            "needs": json_list(result.needs),
            "budget": clip(result.budget, 200),
            "objections": json_list(result.objections),
            "intent_level": result.intent_level,
            "next_action": clip(result.next_action, 500),
            "project_address": clip(result.project_address, 500),
            "province": clip(result.province, 50),
            "city": clip(result.city, 50),
            "contact": clip(result.contact, 200),
            "project_summary": clip(result.project_summary, 1000),
            "longitude": lng,
            "latitude": lat,
            "source_title": clip(row.get("title"), 500),
            "source_url": clip(row.get("url"), 2048),
            "source_url_md5": hashlib.md5(row["url"].encode("utf-8")).hexdigest(),
            "publish_date": clip(row.get("date"), 50),
        }
        # source_url_md5 是唯一键；重复 URL 会返回 rowcount=0，不计入 saved
        rowcount = dao.insert_lead(record)
        saved += 1 if rowcount == 1 else 0

    logger.info("商机抽取入库完成 total=%s saved=%s failed=%s", len(candidates), saved, failed)
    return {"total": len(candidates), "saved": saved, "failed": failed, "failed_rows": failed_rows}


def crawl_and_save(base_domain, list_url):
    """抓取列表页和详情，批量抽取并入库（旧入口，行为不变）。

    流程：
    1. 规范化 base_domain / list_url，填反时自动交换
    2. 同步爬取列表页和全部详情页（htmlhelper 内部有 2~10 秒休眠）
    3. 交给 extract_and_save 做 LLM 抽取、地理编码、去重入库
    """
    # 两个参数填反时自动交换；base_domain 无效时从 list_url 提取域名
    base_domain, list_url = normalize_source(base_domain, list_url)
    if not is_origin(base_domain):
        base_domain = origin(list_url)
    if not base_domain:
        raise BizException(
            "base_domain 无效，请填写站点根域名，例如 https://ggzy.hefei.gov.cn"
        )

    # htmlhelper 是同步串行爬取，选择器硬编码为合肥公共资源交易中心；
    # 请求失败时可能返回空列表，因此空结果需要明确报错。
    rows = run_all_tender_crawl(list_url, base_domain)
    if not rows:
        raise BizException("未抓取到公告，请检查 list_url、base_domain 或站点选择器")

    candidates = [row for row in rows if row.get("url") and row.get("content")]
    if not candidates:
        raise BizException("未解析到有效公告正文，请检查站点选择器")

    result = extract_and_save(candidates)
    return {"total": result["total"], "saved": result["saved"], "failed": result["failed"]}


def get_points():
    """查询地图展示所需的商机点位。"""
    points = dao.list_points()
    for point in points:
        point["project_name"] = (
            point["source_title"] or point["customer"] or "未命名项目"
        )
    return points
