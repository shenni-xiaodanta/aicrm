"""项目总结请求模型。"""
from pydantic import BaseModel, Field


class SummaryRequest(BaseModel):
    lead_id: int = Field(..., ge=1)
