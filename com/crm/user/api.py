"""用户管理接口（子路由，由 com.crm.main 注册）。"""
import logging

from fastapi import APIRouter, Depends, Path, Query, Request

from com.crm.common.response import ok
from com.crm.user import service
from com.crm.user.auth import require_admin, require_login
from com.crm.user.schemas import (
    LoginRequest,
    PasswordRequest,
    RegisterRequest,
    UserUpdateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["用户管理"])


@router.post("/register")
def register(body: RegisterRequest):
    """注册账号（第一个注册用户自动成为管理员）。"""
    return ok(service.register(body.username, body.password, body.nickname), "注册成功")


@router.post("/login")
def login(body: LoginRequest, request: Request):
    """登录并写入会话。"""
    user = service.login(body.username, body.password)
    request.session.clear()
    request.session["uid"] = user["id"]
    request.session["username"] = user["username"]
    request.session["role"] = user["role"]
    return ok(user, "登录成功")


@router.post("/logout")
def logout(request: Request):
    """退出登录。"""
    request.session.clear()
    return ok(msg="已退出登录")


@router.get("/me")
def me(user=Depends(require_login)):
    """当前登录用户。"""
    return ok(user)


@router.get("/page")
def page(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: str = Query("", max_length=50),
    _admin=Depends(require_admin),
):
    """分页查询用户（仅管理员）。"""
    return ok(service.page_users(page, size, keyword))


@router.put("/password")
def change_password(body: PasswordRequest, user=Depends(require_login)):
    """修改当前用户密码。"""
    service.change_password(user["id"], body.old_password, body.new_password)
    return ok(msg="密码修改成功")


@router.put("/update/{user_id}")
def update_user(
    body: UserUpdateRequest,
    user_id: int = Path(..., ge=1),
    _admin=Depends(require_admin),
):
    """修改用户昵称/状态（仅管理员）。"""
    return ok(service.update_user(user_id, body.nickname, body.status), "修改成功")


@router.delete("/del/{user_id}")
def delete_user(
    user_id: int = Path(..., ge=1),
    admin=Depends(require_admin),
):
    """删除用户（仅管理员，不能删除自己）。"""
    service.delete_user(admin, user_id)
    return ok({"id": user_id}, "删除成功")
