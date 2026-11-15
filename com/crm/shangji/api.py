"""商机采集接口（子路由，由 com.crm.main 注册）。"""
import logging
import os

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from com.crm.common.config import STATIC_DIR
from com.crm.common.exceptions import BizException
from com.crm.common.response import fail, ok
from com.crm.shangji import service
from com.crm.shangji.schemas import CrawlRequest
from com.crm.user.auth import require_login

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shangji", tags=["商机"])


@router.post("/crawl")
def crawl(body: CrawlRequest, _user=Depends(require_login)):
    """爬取公告列表并抽取、入库商机（同步等待，可能耗时数分钟）。"""
    try:
        return ok(service.crawl_and_save(body.base_domain, body.list_url), "抓取完成")
    except BizException as exc:
        return fail(exc.msg, code=exc.code)
    except Exception as exc:
        logger.exception("商机采集失败")
        return fail(f"服务器异常：{exc}", code=500)


@router.get("/points")
def points(_user=Depends(require_login)):
    """地图点位数据。"""
    return ok(service.get_points())


@router.get("/map", response_class=HTMLResponse)
def map_page(request: Request):
    """高德地图展示页；未登录跳转登录页。"""
    if not request.session.get("uid"):
        return RedirectResponse("/login")
    key = os.getenv("AMAP_JS_KEY", "")
    security = os.getenv("AMAP_SECURITY_CODE", "")
    config = (
        f'window._AMapSecurityConfig = {{ securityJsCode: "{security}" }};'
        if security else ""
    )
    # 页面是静态 HTML，后端只把高德 key/安全密钥替换进去后返回
    html = (STATIC_DIR / "shangji" / "html" / "map.html").read_text(encoding="utf-8")
    return HTMLResponse(
        html.replace("__AMAP_JS_KEY__", key)
        .replace("__AMAP_SECURITY_CONFIG__", config)
    )
