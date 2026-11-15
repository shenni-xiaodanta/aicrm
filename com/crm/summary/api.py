"""项目总结接口（子路由，由 com.crm.main 注册）。"""
from fastapi import APIRouter, Depends

from com.crm.common.response import ok
from com.crm.summary import service
from com.crm.summary.schemas import SummaryRequest
from com.crm.user.auth import require_login

router = APIRouter(prefix="/summary", tags=["总结"])


@router.get("/detail")
def detail(lead_id: int, _user=Depends(require_login)):
    """查询已保存的项目总结。"""
    return ok(service.get_detail(lead_id))


@router.post("/generate")
def generate(body: SummaryRequest, _user=Depends(require_login)):
    """并行生成标签、摘要、项目分析、经验总结。"""
    return ok(service.generate(body.lead_id), "总结完成")
