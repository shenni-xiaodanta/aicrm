"""用户模块数据模型。"""
import re

from pydantic import BaseModel, Field, field_validator

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,32}$")

def _check_username(value: str) -> str:
    value = (value or "").strip()
    if not USERNAME_RE.fullmatch(value):
        raise ValueError("用户名只能包含 3~32 位字母、数字或下划线")
    return value

class RegisterRequest(BaseModel):
    """注册请求。"""
    username: str
    password: str = Field(..., min_length=6, max_length=64)
    nickname: str = Field("", max_length=50)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        return _check_username(value)

    @field_validator("nickname")
    @classmethod
    def strip_nickname(cls, value: str) -> str:
        return (value or "").strip()


class LoginRequest(BaseModel):
    """登录请求。"""
    username: str = Field(..., min_length=1, max_length=32)
    password: str = Field(..., min_length=1, max_length=64)


class PasswordRequest(BaseModel):
    """修改密码请求。"""
    old_password: str = Field(..., min_length=1, max_length=64)
    new_password: str = Field(..., min_length=6, max_length=64)


class UserUpdateRequest(BaseModel):
    """管理员修改用户资料。"""
    nickname: str = Field("", max_length=50)
    status: int = Field(1, ge=0, le=1)
