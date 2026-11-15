"""概况聊天接口（子路由，由 com.crm.main 注册）。

注意：流式接口刻意使用 HTTPException（HTTP 4xx），而不是项目统一的
HTTP 200 + body.code 约定，因为前端需要区分“请求失败”和“正常文本流”。
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from com.crm.chat import service
from com.crm.chat.schemas import ChatRequest
from com.crm.common.exceptions import BizException
from com.crm.common.response import ok
from com.crm.user.auth import current_user, require_login

router = APIRouter(prefix="/chat", tags=["概况"])


@router.get("/history")
def history(lead_id: int, user=Depends(require_login)):
    """当前登录用户在该项目下的聊天历史。"""
    return ok(service.list_history(lead_id, user["id"]))


@router.post("/stream")
def stream(body: ChatRequest, request: Request):
    """流式回答：纯文本块，前端逐块追加。"""
    # 不能走 require_login：BizException 会被全局处理器转成 HTTP 200 JSON，
    # 前端会把 JSON 当成普通文本追加到聊天气泡里。
    user = current_user(request)
    if not user or int(user.get("status", 1)) != 1:
        raise HTTPException(status_code=401, detail="请先登录")

    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="消息不能为空")

    try:
        messages = service.build_messages(body.lead_id, user["id"], message)
    except BizException as exc:
        raise HTTPException(status_code=400, detail=exc.msg) from exc

    # 先保存用户提问：即使模型调用失败或客户端中断，提问也不会丢
    service.save_message(body.lead_id, user["id"], "user", message)

    # 纯文本流；禁用缓存和代理缓冲，保证前端尽快收到每个分块
    return StreamingResponse(
        service.stream_reply(body.lead_id, user["id"], messages),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
