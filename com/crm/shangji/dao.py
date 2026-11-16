"""商机表 DAO（数据访问层）：只负责 SQL，不做业务判断。"""
import json

from com.crm.common.basedao import execute, query_all

COLUMNS = (
    "customer", "industry", "needs", "budget", "objections",
    "intent_level", "next_action", "project_address", "province", "city",
    "contact", "project_summary", "longitude", "latitude",
    "source_title", "source_url", "source_url_md5", "publish_date",
)

# INSERT IGNORE + source_url_md5 唯一键实现去重：
# 重复 URL 不报错，rowcount=0，调用方据此区分新增和重复。
INSERT_SQL = (
    "INSERT IGNORE INTO crm_shangji "
    f"({', '.join(COLUMNS)}) "
    f"VALUES ({', '.join(['%s'] * len(COLUMNS))})"
)


POINT_COLUMNS = (
    "id", "source_title", "customer", "industry", "needs", "budget",
    "objections", "intent_level", "next_action", "project_address",
    "province", "city", "contact", "project_summary", "longitude", "latitude",
    "source_url", "publish_date",
)


def insert_lead(lead):
    """插入一条商机；重复 URL 由唯一键忽略。返回影响行数（1 新增 / 0 重复）。"""
    return execute(INSERT_SQL, tuple(lead[col] for col in COLUMNS))


def _decode(row):
    """还原 MySQL JSON 字段，供接口直接使用。

    pymysql 对 JSON 列通常返回字符串，但不同版本/驱动也可能返回 bytes
    或已解析对象，这里统一兼容，保证接口拿到的是 list。
    """
    out = dict(row)
    for key in ("needs", "objections"):
        value = out.get(key)
        if isinstance(value, (bytes, bytearray)):
            value = value.decode("utf-8")
        if isinstance(value, (list, dict)):
            out[key] = value
            continue
        try:
            out[key] = json.loads(value) if value else []
        except (TypeError, ValueError):
            out[key] = []
    return out


def list_points():
    """查询全部商机（含未解析出坐标的），列表与地图共用一份数据。

    坐标过滤交给前端：地图只画有经纬度的，无坐标的只在列表展示——
    原来这里 WHERE longitude IS NOT NULL 会把无坐标商机整个藏掉，
    双视图上线后它们必须出现在列表里（状态栏的「共 N 条 · M 条有坐标」）。
    """
    rows = query_all(
        f"SELECT {', '.join(POINT_COLUMNS)} FROM crm_shangji "
        "ORDER BY id DESC",
        None,
    )
    return [_decode(row) for row in rows]
