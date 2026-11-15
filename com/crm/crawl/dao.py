"""采集模块 DAO：站点 / 地区 / 任务三张表的 SQL，不做业务判断。"""
import json

from com.crm.common.basedao import execute, insert, query_all, query_one


def _decode_json_fields(row, *keys):
    """pymysql 对 JSON 列通常返回 str，也可能是 bytes / 已解析对象，
    统一兼容成 dict（与 shangji/dao._decode 同一坑，同一解法）。"""
    out = dict(row)
    for key in keys:
        value = out.get(key)
        if isinstance(value, (bytes, bytearray)):
            value = value.decode("utf-8")
        if isinstance(value, (list, dict)):
            continue
        try:
            out[key] = json.loads(value) if value else {}
        except (TypeError, ValueError):
            out[key] = {}
    return out


# ---------------------------------------------------------------------
# 站点模板
# ---------------------------------------------------------------------
SITE_COLUMNS = (
    "id", "site_code", "site_name", "selectors", "pagination", "charset",
    "render_mode", "request_interval", "max_retry", "max_pages",
    "enabled", "probed_at",
)


def get_site(site_id):
    row = query_one(
        f"SELECT {', '.join(SITE_COLUMNS)} FROM crm_crawl_site WHERE id = %s",
        (site_id,),
    )
    return _decode_json_fields(row, "selectors", "pagination") if row else None


def list_sites():
    rows = query_all(
        f"SELECT {', '.join(SITE_COLUMNS)} FROM crm_crawl_site ORDER BY id",
        None,
    )
    return [_decode_json_fields(row, "selectors", "pagination") for row in rows]


def update_site(site_id, fields):
    """按传入字段更新站点配方（调用方负责校验内容合法）。"""
    if not fields:
        return 0
    set_sql = ", ".join(f"{key} = %s" for key in fields)
    args = list(fields.values()) + [site_id]
    return execute(
        f"UPDATE crm_crawl_site SET {set_sql} WHERE id = %s", tuple(args)
    )


# ---------------------------------------------------------------------
# 地区采集点
# ---------------------------------------------------------------------
# s_ 前缀 = 来自 join 的站点表字段，避免与地区字段重名
_REGION_SELECT = (
    "SELECT r.id, r.site_id, r.province, r.city, r.list_url, r.enabled, "
    "r.last_task_id, r.last_crawl_at, "
    "s.site_code, s.site_name, s.render_mode AS s_render_mode, "
    "s.enabled AS s_enabled "
    "FROM crm_crawl_region r "
    "JOIN crm_crawl_site s ON s.id = r.site_id"
)


def get_region(region_id):
    return query_one(f"{_REGION_SELECT} WHERE r.id = %s", (region_id,))


def list_regions():
    return query_all(f"{_REGION_SELECT} ORDER BY r.province, r.city", None)


def touch_region(region_id, task_id):
    """采集结束时回写地区行的最近任务/时间，供列表页直显。"""
    execute(
        "UPDATE crm_crawl_region SET last_task_id = %s, last_crawl_at = NOW() "
        "WHERE id = %s",
        (task_id, region_id),
    )


# ---------------------------------------------------------------------
# 采集任务
# ---------------------------------------------------------------------
_TASK_SELECT = (
    "SELECT t.*, r.province, r.city, s.site_code "
    "FROM crm_crawl_task t "
    "JOIN crm_crawl_region r ON r.id = t.region_id "
    "JOIN crm_crawl_site s ON s.id = t.site_id"
)


def create_task(region_id, site_id, triggered_by):
    return insert(
        "INSERT INTO crm_crawl_task (region_id, site_id, triggered_by, status) "
        "VALUES (%s, %s, %s, 'running')",
        (region_id, site_id, triggered_by),
    )


def update_task(task_id, fields):
    """按传入字段更新任务进度/结果（key → 值，值直接参数化）。"""
    if not fields:
        return 0
    set_sql = ", ".join(f"{key} = %s" for key in fields)
    args = list(fields.values()) + [task_id]
    return execute(
        f"UPDATE crm_crawl_task SET {set_sql} WHERE id = %s", tuple(args)
    )


def get_task(task_id):
    row = query_one(f"{_TASK_SELECT} WHERE t.id = %s", (task_id,))
    return _decode_json_fields(row, "fail_detail") if row else None


def list_tasks(limit=50):
    rows = query_all(
        f"{_TASK_SELECT} ORDER BY t.id DESC LIMIT %s", (min(limit, 200),)
    )
    return [_decode_json_fields(row, "fail_detail") for row in rows]


def running_task_for_site(site_id):
    """单站锁查询：同站同时只允许一个运行中任务。

    不用数据库唯一约束做这件事——status 会从 running 变走，
    唯一约束表达不了"运行中唯一"，只能代码锁。
    """
    return query_one(
        "SELECT id FROM crm_crawl_task WHERE site_id = %s AND status = 'running'",
        (site_id,),
    )


# ---------------------------------------------------------------------
# 商机去重（读 crm_shangji，采集增量停止的判据）
# ---------------------------------------------------------------------
def lead_exists(source_url_md5):
    return query_one(
        "SELECT id FROM crm_shangji WHERE source_url_md5 = %s LIMIT 1",
        (source_url_md5,),
    )
