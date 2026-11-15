"""负责人变更请求模型。"""
from pydantic import BaseModel, Field


class OwnerChangeRequest(BaseModel):
    lead_id: int = Field(..., ge=1)
    owner_id: int = Field(..., ge=1)
    note: str = Field("", max_length=500)
