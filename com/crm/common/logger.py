# -*- coding: utf-8 -*-
"""
request_id 贯穿日志

解决什么问题：原项目日志只有「时间 + 线程 + 模块 + 消息」，一次采集失败
打印了十几条日志，事后没法确认哪些行属于同一次请求。这里给每个请求生成
一个短 id，写日志时自动带上，响应头也回传（X-Request-ID），
前端报障时把这个 id 发过来，后端 grep 一下就能拉出完整链路。

三件套：
- RequestIDMiddleware：每请求生成 id，存 contextvars，写入响应头
- current_request_id()：业务代码需要把 id 放进业务数据（如错误返回）时取用
- RequestContextFilter：给日志记录打上 request_id 属性（必须挂在 handler 上，
  挂在 logger 上的 Filter 只对直接调用 logger 的记录生效，会漏掉子模块的日志）
"""
import logging
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# 默认 "-"：不在 HTTP 请求上下文里（启动脚本、定时任务）时格式化不报 KeyError
request_id_ctx: ContextVar = ContextVar("request_id", default="-")


def current_request_id() -> str:
    """取当前请求的 request_id；不在请求上下文中返回 "-"。"""
    return request_id_ctx.get()


class RequestContextFilter(logging.Filter):
    """把 request_id 注入每条日志记录。挂在 config.py 的两个 handler 上。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


class RequestIDMiddleware(BaseHTTPMiddleware):
    """为每个请求生成并贯穿 request_id。

    放在 SessionMiddleware 之后安装（Starlette 后添加的在外层先执行），
    保证连登录跳转这类响应也带 id。
    """

    async def dispatch(self, request: Request, call_next):
        # 12 位足够一次排障用，且日志行不会太宽；碰撞概率按天日志量可忽略
        rid = uuid.uuid4().hex[:12]
        token = request_id_ctx.set(rid)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            request_id_ctx.reset(token)
