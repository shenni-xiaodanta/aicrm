"""登录态校验。"""
from fastapi import Request

from com.crm.common.exceptions import BizException
from com.crm.user import dao


def current_user(request: Request):
    """从会话中取当前用户，未登录返回 None。"""
    user_id = request.session.get("uid")
    return dao.get_by_id(user_id) if user_id else None


def require_login(request: Request):
    """接口登录校验。

    session 里只存 uid，这里每次重新查库：
    - 账号被禁用/删除后立即生效，不用等 session 过期
    - 返回完整用户信息，供接口做角色判断
    """
    user = current_user(request)
    if not user:
        raise BizException("请先登录", code=401)
    if int(user.get("status", 1)) != 1:
        request.session.clear()
        raise BizException("账号已被禁用", code=403)
    return user


def require_admin(request: Request):
    """管理员权限校验。"""
    user = require_login(request)
    if user.get("role") != "admin":
        raise BizException("无权限访问", code=403)
    return user
