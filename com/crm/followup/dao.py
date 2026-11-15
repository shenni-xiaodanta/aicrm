"""跟进记录 DAO（数据访问层）。"""
from com.crm.common.basedao import execute, insert, query_all, query_one


def insert_follow_up(lead_id, content, created_by=None):
    """新增跟进记录，返回自增主键。created_by 由 001_baseline.sql 起启用。"""
    return insert(
        "INSERT INTO crm_follow_up (lead_id, content, created_by) VALUES (%s, %s, %s)",
        (lead_id, content, created_by),
    )


def insert_file(follow_up_id, lead_id, original_name, stored_name, file_size, content_type):
    """新增附件记录。"""
    return insert(
        "INSERT INTO crm_follow_up_file "
        "(follow_up_id, lead_id, original_name, stored_name, file_size, content_type) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (follow_up_id, lead_id, original_name, stored_name, file_size, content_type),
    )


def list_by_lead(lead_id):
    """按时间倒序查询某条商机的跟进记录及附件。"""
    rows = query_all(
        "SELECT id, lead_id, content, create_time FROM crm_follow_up "
        "WHERE lead_id = %s ORDER BY create_time DESC, id DESC",
        (lead_id,),
    )
    if not rows:
        return []

    ids = [row["id"] for row in rows]
    placeholders = ", ".join(["%s"] * len(ids))
    files = query_all(
        f"SELECT id, follow_up_id, original_name, file_size, content_type "
        f"FROM crm_follow_up_file WHERE follow_up_id IN ({placeholders}) ORDER BY id",
        ids,
    )

    grouped = {}
    for file in files:
        grouped.setdefault(file["follow_up_id"], []).append(file)
    for row in rows:
        row["files"] = grouped.get(row["id"], [])
        if hasattr(row["create_time"], "strftime"):
            row["create_time"] = row["create_time"].strftime("%Y-%m-%d %H:%M:%S")
    return rows


def get_file(file_id):
    """查询附件元数据，join 主记录取 created_by（下载归属校验用）。

    lead_id 直接取文件表冗余列；created_by 只在主记录上，
    用 LEFT JOIN 而不是两次查询：文件行一定有 follow_up_id，合并一次拿全。
    """
    return query_one(
        "SELECT f.id, f.lead_id, fu.created_by, f.original_name, f.stored_name, "
        "f.file_size, f.content_type "
        "FROM crm_follow_up_file f "
        "LEFT JOIN crm_follow_up fu ON fu.id = f.follow_up_id "
        "WHERE f.id = %s",
        (file_id,),
    )


def get_lead_owner(lead_id):
    """查询商机负责人，下载鉴权用；商机不存在返回 None。"""
    return query_one(
        "SELECT owner_id FROM crm_shangji WHERE id = %s", (lead_id,)
    )


def delete_follow_up(follow_up_id):
    """删除跟进记录及其附件记录（用于写入失败时回滚）。"""
    execute(
        "DELETE FROM crm_follow_up_file WHERE follow_up_id = %s", (follow_up_id,)
    )
    execute("DELETE FROM crm_follow_up WHERE id = %s", (follow_up_id,))
