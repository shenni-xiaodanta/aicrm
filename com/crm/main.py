"""CRM FastAPI 入口：注册子路由 + 统一异常处理。"""
import logging

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

load_dotenv(override=False)

import com.crm.common.config
from com.crm.common.config import SESSION_MAX_AGE, SESSION_SECRET, STATIC_DIR
from com.crm.common.exceptions import BizException
from com.crm.attachment.api import router as attachment_router
from com.crm.chat.api import router as chat_router
from com.crm.common.response import fail
from com.crm.followup.api import router as followup_router
from com.crm.owner.api import router as owner_router
from com.crm.source.api import router as source_router
from com.crm.summary.api import router as summary_router
from com.crm.user.api import router as user_router
from com.crm.shangji.api import map_page, router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="CRM 商机采集服务",
    version="1.0.0",
    description="爬取招标/采购公告，LLM 结构化抽取，地理编码并保存商机",
)

# SessionMiddleware 必须在路由之前安装：它把签名后的 session 放进 request.scope，
# 后面所有 request.session 访问都依赖它。上线建议 https_only=True。
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    max_age=SESSION_MAX_AGE,
    # 控制 Cookie 的 SameSite 属性
    #现代浏览器默认值，安全性和可用性平衡，跨站 POST / fetch / iframe不发送
    same_site="lax",
    # 控制 Cookie 的 Secure 属性
    https_only=False,   # 本地开发用 HTTP；上线改成 True
)
# 各业务路由自行通过 Depends(require_login) 做鉴权；/static 最后挂载，避免遮挡 API 路由。
app.include_router(router)
app.include_router(user_router)
app.include_router(source_router)
app.include_router(followup_router) # 跟进
app.include_router(attachment_router)  # 附件
app.include_router(chat_router)
app.include_router(owner_router)  # 负责人
app.include_router(summary_router)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ---- 全局异常处理（HTTP 状态始终 200，失败信息放在 code）----
# 统一约定：所有业务响应都是 HTTP 200，失败信息放在 body.code。
# 例外：/chat/stream 使用 HTTPException，因为流式响应无法用 JSON 信封表达错误。
@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    """参数校验失败 -> 统一格式"""
    logger.error(f"请求 {request.url.path} 参数错误：{exc}")
    err = exc.errors()[0] if exc.errors() else {}
    return JSONResponse(
        status_code=200,
        content=fail(f"参数错误：{err.get('msg', '请检查提交内容')}", code=422),
    )


@app.exception_handler(BizException)
async def biz_exception_handler(request: Request, exc: BizException):
    """业务异常：资源不存在等，返回业务码（不当作系统故障）"""
    logger.warning(f"请求 {request.url.path} 业务异常：{exc.msg}")
    return JSONResponse(status_code=200, content=fail(exc.msg, code=exc.code))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """兜底：系统异常"""
    logger.error(f"请求 {request.url.path} 发生系统异常：{exc}")
    return JSONResponse(
        status_code=200,
        content=fail(f"服务器异常：{exc}", code=500),
    )


@app.get("/login", include_in_schema=False)
def login_page(request: Request):
    """登录页；已登录则回首页。"""
    if request.session.get("uid"):
        return RedirectResponse("/")
    return FileResponse(STATIC_DIR / "user" / "html" / "login.html")


@app.get("/register", include_in_schema=False)
def register_page(request: Request):
    """注册页；已登录则回首页。"""
    if request.session.get("uid"):
        return RedirectResponse("/")
    return FileResponse(STATIC_DIR / "user" / "html" / "register.html")


@app.get("/", include_in_schema=False)
def root(request: Request):
    """首页：登录后展示商机地图。"""
    if not request.session.get("uid"):
        return RedirectResponse("/login")
    # map_page 内部也会做一次登录校验；这里直接调用函数，不经过依赖注入
    return map_page(request)


if __name__ == "__main__":
    uvicorn.run("com.crm.main:app", host="0.0.0.0", port=8001, reload=True)

