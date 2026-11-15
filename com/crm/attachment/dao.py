"""附件管理 DAO（数据访问层）。"""
from com.crm.common.basedao import execute, insert, query_all, query_one


def insert_record(lead_id, category, description):
    """新增附件记录，返回自增主键。"""
    return insert(
        "INSERT INTO crm_attachment_record (lead_id, category, description) "
        "VALUES (%s, %s, %s)",
        (lead_id, category, description),
    )


def insert_file(record_id, lead_id, original_name, stored_name, file_size, content_type):
    """新增附件文件记录。"""
    return insert(
        "INSERT INTO crm_attachment_file "
        "(record_id, lead_id, original_name, stored_name, file_size, content_type) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (record_id, lead_id, original_name, stored_name, file_size, content_type),
    )


def list_by_lead(lead_id):
    """按时间倒序查询某条商机的附件记录及文件。"""
    rows = query_all(
        "SELECT id, lead_id, category, description, create_time "
        "FROM crm_attachment_record WHERE lead_id = %s "
        "ORDER BY create_time DESC, id DESC",
        (lead_id,),
    )
    if not rows:
        return []

    ids = [row["id"] for row in rows]
    placeholders = ", ".join(["%s"] * len(ids))
    files = query_all(
        f"SELECT id, record_id, original_name, file_size, content_type "
        f"FROM crm_attachment_file WHERE record_id IN ({placeholders}) ORDER BY id",
        ids,
    )

    grouped = {}
    for file in files:
        grouped.setdefault(file["record_id"], []).append(file)
    for row in rows:
        row["files"] = grouped.get(row["id"], [])
        if hasattr(row["create_time"], "strftime"):
            row["create_time"] = row["create_time"].strftime("%Y-%m-%d %H:%M:%S")
    return rows


def get_file(file_id):
    """查询附件文件元数据。"""
    return query_one(
        "SELECT id, original_name, stored_name, file_size, content_type "
        "FROM crm_attachment_file WHERE id = %s",
        (file_id,),
    )


def delete_record(record_id):
    """删除附件记录及文件记录（用于写入失败时回滚）。"""
    execute("DELETE FROM crm_attachment_file WHERE record_id = %s", (record_id,))
    execute("DELETE FROM crm_attachment_record WHERE id = %s", (record_id,))
