"""负责人接口（子路由，由 com.crm.main 注册）。"""
from fastapi import APIRouter, Depends

from com.crm.common.response import ok
from com.crm.owner import service
from com.crm.owner.schemas import OwnerChangeRequest
from com.crm.user.auth import require_login

router = APIRouter(prefix="/owner", tags=["负责人"])


@router.get("/detail")
def detail(lead_id: int, _user=Depends(require_login)):
    """当前负责人、可选用户、变更记录。"""
    return ok(service.get_detail(lead_id))


@router.post("/change")
def change(body: OwnerChangeRequest, user=Depends(require_login)):
    """变更负责人并记录变更。"""
    return ok(
        service.change_owner(body.lead_id, body.owner_id, body.note, user["id"]),
        "变更成功",
    )
