"""负责人 DAO（数据访问层）。"""
from com.crm.common.basedao import execute, insert, query_all, query_one


def get_lead(lead_id):
    return query_one(
        "SELECT id, owner_id FROM crm_shangji WHERE id = %s", (lead_id,)
    )


def get_user(user_id):
    return query_one(
        "SELECT id, username, nickname FROM crm_user WHERE id = %s", (user_id,)
    )


def list_users():
    """可选负责人：启用状态的用户。"""
    return query_all(
        "SELECT id, username, nickname FROM crm_user WHERE status = 1 ORDER BY id"
    )


def update_owner(lead_id, owner_id):
    return execute(
        "UPDATE crm_shangji SET owner_id = %s WHERE id = %s", (owner_id, lead_id)
    )


def insert_change(lead_id, old_owner_id, new_owner_id, note, operator_id):
    return insert(
        "INSERT INTO crm_owner_change "
        "(lead_id, old_owner_id, new_owner_id, note, operator_id) "
        "VALUES (%s, %s, %s, %s, %s)",
        (lead_id, old_owner_id, new_owner_id, note, operator_id),
    )


def list_changes(lead_id):
    """按时间倒序返回负责人变更记录。"""
    rows = query_all(
        "SELECT c.id, c.note, c.create_time, "
        "ou.username AS old_username, ou.nickname AS old_nickname, "
        "nu.username AS new_username, nu.nickname AS new_nickname "
        "FROM crm_owner_change c "
        "LEFT JOIN crm_user ou ON ou.id = c.old_owner_id "
        "LEFT JOIN crm_user nu ON nu.id = c.new_owner_id "
        "WHERE c.lead_id = %s ORDER BY c.id DESC",
        (lead_id,),
    )
    for row in rows:
        old_nickname = row.pop("old_nickname")
        old_username = row.pop("old_username")
        new_nickname = row.pop("new_nickname")
        new_username = row.pop("new_username")
        row["old_name"] = old_nickname or old_username or "未指定"
        row["new_name"] = new_nickname or new_username or "未指定"
        if hasattr(row["create_time"], "strftime"):
            row["create_time"] = row["create_time"].strftime("%Y-%m-%d %H:%M:%S")
    return rows
