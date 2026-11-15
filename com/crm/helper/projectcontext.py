"""项目资料上下文：商机、跟进、招投标/立项。"""
import json
import logging

from com.crm.attachment import service as attachment_service
from com.crm.common.basedao import query_one
from com.crm.common.exceptions import BizException
from com.crm.followup import service as followup_service

logger = logging.getLogger(__name__)

MAX_CONTEXT_CHARS = 8000


def get_lead(lead_id):
    """查询组装上下文所需的商机字段。"""
    return query_one(
        "SELECT source_title, customer, industry, needs, budget, objections, "
        "intent_level, next_action, project_address, province, city, contact, "
        "project_summary, source_url, publish_date "
        "FROM crm_shangji WHERE id = %s",
        (lead_id,),
    )


def _fmt_json(value):
    """把 needs / objections 的 JSON 字段转成可读文本。"""
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return value
    if isinstance(value, (list, tuple)):
        return "、".join(str(item) for item in value)
    return str(value)


def build_project_context(lead_id):
    """组装商机、跟进、招投标/立项资料，供聊天和总结共用。

    - 只按 lead_id 读取，项目资料对所有登录用户共享
    - 跟进最多 20 条、附件最多 30 条，最终截断到 8000 字
    - 子表读取失败只记日志并降级，避免聊天/总结整体不可用
    """
    lead = get_lead(lead_id)
    if not lead:
        raise BizException("商机不存在", code=1000)

    lines = [
        "【商机】",
        f"项目名称：{lead.get('source_title') or ''}",
        f"客户/招标人：{lead.get('customer') or ''}",
        f"行业：{lead.get('industry') or ''}",
        f"意向等级：{lead.get('intent_level') or ''}",
        f"预算：{lead.get('budget') or ''}",
        f"地区：{(lead.get('province') or '')} {(lead.get('city') or '')}".strip(),
        f"项目地址：{lead.get('project_address') or ''}",
        f"联系方式：{lead.get('contact') or ''}",
        f"需求：{_fmt_json(lead.get('needs'))}",
        f"风险/限制：{_fmt_json(lead.get('objections'))}",
        f"下一步：{lead.get('next_action') or ''}",
        f"概述：{lead.get('project_summary') or ''}",
        f"发布日期：{lead.get('publish_date') or ''}",
        f"原文：{lead.get('source_url') or ''}",
    ]

    # 跟进/附件表缺失或读取失败时降级为空，不影响商机本身的问答
    try:
        followups = followup_service.list_follow_ups(lead_id)
    except Exception:
        logger.warning("读取跟进记录失败 lead_id=%s", lead_id)
        followups = []
    if followups:
        lines.append("【跟进记录】")
        for item in followups[:20]:
            files = "、".join(
                file.get("original_name", "") for file in item.get("files", [])
            )
            text = f"- {item.get('create_time', '')} {item.get('content', '')}"
            if files:
                text += f"（附件：{files}）"
            lines.append(text)

    try:
        attachments = attachment_service.list_attachments(lead_id)
    except Exception:
        logger.warning("读取附件记录失败 lead_id=%s", lead_id)
        attachments = []
    if attachments:
        lines.append("【招投标/立项资料】")
        for item in attachments[:30]:
            files = "、".join(
                file.get("original_name", "") for file in item.get("files", [])
            )
            text = (
                f"- [{item.get('category', '')}] "
                f"{item.get('create_time', '')} {item.get('description', '')}"
            )
            if files:
                text += f"（附件：{files}）"
            lines.append(text)

    # 控制送给模型的上下文长度，避免超出模型窗口
    return "\n".join(lines)[:MAX_CONTEXT_CHARS]
