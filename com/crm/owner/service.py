"""负责人业务层：当前负责人、可选用户、变更记录。"""
import logging

from com.crm.common.db import tx
from com.crm.common.exceptions import BizException
from com.crm.owner import dao

logger = logging.getLogger(__name__)


def _name(user):
    """优先昵称，其次用户名；用户不存在时显示“未指定”。"""
    if not user:
        return "未指定"
    return user.get("nickname") or user.get("username") or "未指定"


def get_detail(lead_id):
    """返回当前负责人、可选用户和变更记录。"""
    lead = dao.get_lead(lead_id)
    if not lead:
        raise BizException("商机不存在", code=1000)

    owner = dao.get_user(lead["owner_id"]) if lead.get("owner_id") else None
    users = [
        {"id": user["id"], "name": _name(user)}
        for user in dao.list_users()
    ]
    return {
        "owner_id": lead.get("owner_id") or 0,
        "owner_name": _name(owner),
        "users": users,
        "changes": dao.list_changes(lead_id),
    }


def change_owner(lead_id, owner_id, note, operator_id):
    """变更负责人并写入变更记录。

    两步写包进同一事务（common/db.py 的 tx()）：原来 update_owner 和
    insert_change 各自提交，极端情况下负责人已改但变更记录丢失——
    负责人口径就断了溯源。现在要么都成、要么都不成。
    """
    lead = dao.get_lead(lead_id)
    if not lead:
        raise BizException("商机不存在", code=1000)
    if not dao.get_user(owner_id):
        raise BizException("负责人不存在", code=1000)

    old_owner_id = lead.get("owner_id") or 0
    # 没有变化直接拒绝，避免产生无意义的变更记录
    if old_owner_id == owner_id:
        raise BizException("负责人未变化", code=1000)

    # 校验（读）放在事务外，事务里只做写：缩短连接占用时间
    with tx():
        dao.update_owner(lead_id, owner_id)
        dao.insert_change(
            lead_id, old_owner_id, owner_id, (note or "").strip()[:500], operator_id
        )
    logger.info(
        "负责人变更 lead_id=%s old=%s new=%s", lead_id, old_owner_id, owner_id
    )
    return get_detail(lead_id)
