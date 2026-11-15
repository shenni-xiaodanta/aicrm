"""聊天记录 DAO（数据访问层）。"""
from com.crm.common.basedao import insert, query_all


def insert_message(lead_id, user_id, role, content):
    """新增一条聊天消息。"""
    return insert(
        "INSERT INTO crm_chat_message (lead_id, user_id, role, content) "
        "VALUES (%s, %s, %s, %s)",
        (lead_id, user_id, role, content),
    )


def list_history(lead_id, user_id, limit=50):
    """查询某用户在某项目下的最近聊天记录，返回时间正序。"""
    rows = query_all(
        "SELECT id, role, content, create_time FROM crm_chat_message "
        "WHERE lead_id = %s AND user_id = %s ORDER BY id DESC LIMIT %s",
        (lead_id, user_id, limit),
    )
    return list(reversed(rows))
