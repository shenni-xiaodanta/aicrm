"""采集源配置数据模型。"""
from pydantic import BaseModel, Field


class SourceRequest(BaseModel):
    """每个地级市保存一套 base_domain / list_url。"""
    province: str = Field(..., min_length=1, max_length=50)
    city: str = Field(..., min_length=1, max_length=50)
    base_domain: str = Field(..., min_length=1, max_length=255)
    list_url: str = Field(..., min_length=1, max_length=2048)
