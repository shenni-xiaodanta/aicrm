"""请求与 LLM 抽取结果模型。"""
from typing import Literal
from pydantic import BaseModel, Field

class CrawlRequest(BaseModel):
    """爬取请求：只需要站点根域名和列表页地址。"""
    base_domain: str = Field(..., min_length=1, max_length=255)
    list_url: str = Field(..., min_length=1, max_length=2048)

class LeadExtraction(BaseModel):
    """LLM 从公告正文中抽取出的商机。"""
    customer: str = ""
    industry: str = ""
    needs: list[str] = Field(default_factory=list)
    budget: str = ""
    objections: list[str] = Field(default_factory=list)
    intent_level: Literal["高", "中", "低"] = "中"
    next_action: str = ""
    longitude: float | None = Field(default=None, ge=-180, le=180)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    project_address: str = ""
    province: str = ""
    city: str = ""
    contact: str = ""
    project_summary: str = ""
