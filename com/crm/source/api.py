"""采集源配置接口（子路由，由 com.crm.main 注册）。"""
from fastapi import APIRouter, Depends, Query

from com.crm.common.response import ok
from com.crm.source import service
from com.crm.source.schemas import SourceRequest
from com.crm.user.auth import require_login

router = APIRouter(prefix="/source", tags=["采集源配置"])


@router.get("/get")
def get_source(
    province: str = Query(..., min_length=1, max_length=50),
    city: str = Query(..., min_length=1, max_length=50),
    _user=Depends(require_login),
):
    """查询某个地级市已保存的采集源配置。"""
    return ok(service.get_source(province, city))


@router.post("/save")
def save_source(body: SourceRequest, _user=Depends(require_login)):
    """保存某个地级市的采集源配置。"""
    return ok(
        service.save_source(
            body.province, body.city, body.base_domain, body.list_url
        ),
        "保存成功",
    )
