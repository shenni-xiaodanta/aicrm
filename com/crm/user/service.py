"""用户模块业务层：注册、登录、密码校验、用户管理。"""
import hashlib
import hmac
import logging
import os

from com.crm.common.exceptions import BizException
from com.crm.user import dao

logger = logging.getLogger(__name__)

# 迭代次数决定哈希成本；调高更安全但登录更慢。
# 哈希串里保存了自身 iterations，改值后旧密码仍能按原参数校验。
PBKDF2_ITERATIONS = 200_000


def hash_password(password):
    """PBKDF2-HMAC-SHA256 加盐哈希。"""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    """校验密码，格式：pbkdf2_sha256$iterations$salt_hex$digest_hex。"""
    try:
        algo, iterations, salt_hex, digest_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        # 常量时间比较，避免根据比较耗时推测正确摘要
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (AttributeError, ValueError):
        return False


def _public(row):
    """去掉密码哈希，返回可安全输出的用户信息。"""
    return {key: value for key, value in row.items() if key != "password_hash"}


def register(username, password, nickname):
    """注册用户；第一个注册的用户自动成为管理员。"""
    if dao.get_by_username(username):
        raise BizException("用户名已存在", code=1000)

    # 注意：count 和 insert 不是原子操作，并发首次注册可能产生多个 admin；
    # 当前靠用户名唯一键兜底，生产环境可加锁或事务。
    role = "admin" if dao.count() == 0 else "user"
    user_id = dao.insert_user(
        username, hash_password(password), nickname or username, role
    )
    logger.info("注册用户 id=%s username=%s role=%s", user_id, username, role)
    return dao.get_by_id(user_id)


def login(username, password):
    """校验账号密码，返回公开用户信息。"""
    row = dao.get_by_username(username)
    if not row or not verify_password(password, row["password_hash"]):
        raise BizException("用户名或密码错误", code=1000)
    if int(row.get("status", 1)) != 1:
        raise BizException("账号已被禁用", code=403)
    return _public(row)


def get_user(user_id):
    """查询用户公开信息。"""
    row = dao.get_by_id(user_id)
    if not row:
        raise BizException("用户不存在", code=1000)
    return row


def page_users(page=1, size=10, keyword=""):
    """分页查询用户；页码最小 1，每页最多 100 条。"""
    page = max(1, int(page))
    size = min(max(1, int(size)), 100)
    keyword = (keyword or "").strip()
    rows, total = dao.page(page, size, keyword)
    return {"total": total, "page": page, "size": size, "rows": rows}


def change_password(user_id, old_password, new_password):
    """校验旧密码后更新为新密码。"""
    row = dao.get_auth_by_id(user_id)
    if not row:
        raise BizException("用户不存在", code=1000)
    if not verify_password(old_password, row["password_hash"]):
        raise BizException("原密码错误", code=1000)
    dao.update_password(user_id, hash_password(new_password))
    logger.info("修改密码 user_id=%s", user_id)


def update_user(user_id, nickname, status):
    """管理员修改昵称和启用状态。"""
    if not dao.get_by_id(user_id):
        raise BizException("用户不存在", code=1000)
    dao.update_user(user_id, nickname or "", status)
    logger.info("修改用户 user_id=%s status=%s", user_id, status)
    return dao.get_by_id(user_id)


def delete_user(operator, user_id):
    """删除用户；不允许删除当前登录用户。"""
    if int(operator["id"]) == int(user_id):
        raise BizException("不能删除当前登录用户", code=1000)
    if not dao.get_by_id(user_id):
        raise BizException("用户不存在", code=1000)
    dao.delete(user_id)
    logger.info("删除用户 user_id=%s operator=%s", user_id, operator["id"])
