"""用户表 DAO（数据访问层）：只负责 SQL。"""
from com.crm.common.basedao import execute, insert, query_all, query_one

TABLE = "crm_user"
PUBLIC_COLUMNS = "id, username, nickname, role, status, create_time, update_time"


def get_by_username(username):
    """登录用：返回含 password_hash 的完整记录。"""
    return query_one(f"SELECT * FROM {TABLE} WHERE username = %s", (username,))


def get_by_id(user_id):
    """查询公开信息（不含密码哈希）。"""
    return query_one(
        f"SELECT {PUBLIC_COLUMNS} FROM {TABLE} WHERE id = %s", (user_id,)
    )


def get_auth_by_id(user_id):
    """修改密码用：返回含 password_hash 的完整记录。"""
    return query_one(f"SELECT * FROM {TABLE} WHERE id = %s", (user_id,))


def count():
    """用户总数，用于判断第一个注册用户是否为管理员。"""
    return query_one(f"SELECT COUNT(*) AS total FROM {TABLE}")["total"]


def insert_user(username, password_hash, nickname, role):
    """新增用户，返回自增主键。"""
    sql = (
        f"INSERT INTO {TABLE} (username, password_hash, nickname, role) "
        "VALUES (%s, %s, %s, %s)"
    )
    return insert(sql, (username, password_hash, nickname, role))


def page(page, size, keyword=""):
    """分页查询用户，返回 (rows, total)。"""
    where, args = "", []
    if keyword:
        where = " WHERE (username LIKE %s OR nickname LIKE %s)"
        like = f"%{keyword}%"
        args = [like, like]

    total = query_one(
        f"SELECT COUNT(*) AS total FROM {TABLE}{where}", args or None
    )["total"]
    rows = query_all(
        f"SELECT {PUBLIC_COLUMNS} FROM {TABLE}{where} "
        "ORDER BY id DESC LIMIT %s OFFSET %s",
        [*args, size, (page - 1) * size],
    )
    return rows, total


def update_password(user_id, password_hash):
    return execute(
        f"UPDATE {TABLE} SET password_hash = %s WHERE id = %s",
        (password_hash, user_id),
    )


def update_user(user_id, nickname, status):
    return execute(
        f"UPDATE {TABLE} SET nickname = %s, status = %s WHERE id = %s",
        (nickname, status, user_id),
    )


def delete(user_id):
    return execute(f"DELETE FROM {TABLE} WHERE id = %s", (user_id,))
