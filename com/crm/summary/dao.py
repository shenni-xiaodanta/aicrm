"""项目总结 DAO（数据访问层）。"""
from com.crm.common.basedao import execute, query_one


def get_summary(lead_id):
    return query_one(
        "SELECT id, lead_id, tags, summary, analysis, lessons, update_time "
        "FROM crm_summary WHERE lead_id = %s",
        (lead_id,),
    )


def upsert_summary(lead_id, tags, summary, analysis, lessons):
    """按商机 ID 新增或更新总结。"""
    sql = (
        "INSERT INTO crm_summary (lead_id, tags, summary, analysis, lessons) "
        "VALUES (%s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE "
        "tags = VALUES(tags), summary = VALUES(summary), "
        "analysis = VALUES(analysis), lessons = VALUES(lessons)"
    )
    return execute(sql, (lead_id, tags, summary, analysis, lessons))
