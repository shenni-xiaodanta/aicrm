"""概况聊天请求模型。"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    lead_id: int = Field(..., ge=1)
    message: str = Field(..., min_length=1, max_length=2000)
