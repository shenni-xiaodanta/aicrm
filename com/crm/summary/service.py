"""项目总结业务层：四项并行分析并保存。"""
import json
import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel

from com.crm.common.exceptions import BizException
from com.crm.common.llm import llm
from com.crm.helper.projectcontext import build_project_context
from com.crm.summary import dao
from com.crm.summary.prompts import (
    analysis_prompt,
    lessons_prompt,
    summary_prompt,
    tags_prompt,
)

logger = logging.getLogger(__name__)

tags_chain = tags_prompt | llm | StrOutputParser()
summary_chain = summary_prompt | llm | StrOutputParser()
analysis_chain = analysis_prompt | llm | StrOutputParser()
lessons_chain = lessons_prompt | llm | StrOutputParser()

# 四项并行执行。key 必须与 generate() 里 result.get(...) 的 key 保持一致，
# 修改字段名时两处要同步。
parallel_chain = RunnableParallel(
    tags=tags_chain,
    summary=summary_chain,
    analysis=analysis_chain,
    lessons=lessons_chain,
)


def _parse_tags(text):
    """把模型返回的标签文本统一成列表。

    兼容中文逗号、顿号、换行，去掉 # 前缀，去重并最多保留 8 个。
    """
    tags = []
    text = (text or "").replace("，", ",").replace("、", ",").replace("\n", ",")
    for item in text.split(","):
        item = item.strip().lstrip("#").strip()
        if item and item not in tags:
            tags.append(item)
    return tags[:8]


def _decode(row):
    """还原数据库中的 tags（JSON 字符串/bytes/已解析列表）并格式化更新时间。"""
    if not row:
        return None
    tags = row.get("tags")
    if isinstance(tags, (str, bytes, bytearray)):
        if isinstance(tags, (bytes, bytearray)):
            tags = tags.decode("utf-8")
        try:
            tags = json.loads(tags)
        except ValueError:
            tags = []
    row["tags"] = tags or []
    if hasattr(row.get("update_time"), "strftime"):
        row["update_time"] = row["update_time"].strftime("%Y-%m-%d %H:%M:%S")
    return row


def get_detail(lead_id):
    """查询已保存的总结。"""
    if int(lead_id) <= 0:
        raise BizException("商机ID无效", code=1000)
    return _decode(dao.get_summary(int(lead_id)))


def generate(lead_id):
    """并行生成标签、摘要、项目分析、经验总结并保存。"""
    lead_id = int(lead_id)
    if lead_id <= 0:
        raise BizException("商机ID无效", code=1000)

    context = build_project_context(lead_id)
    result = parallel_chain.invoke({"context": context})

    tags = _parse_tags(result.get("tags"))
    summary = (result.get("summary") or "").strip()
    analysis = (result.get("analysis") or "").strip()
    lessons = (result.get("lessons") or "").strip()
    if not (tags or summary or analysis or lessons):
        raise BizException("总结失败，请稍后重试", code=1000)

    # tags 以 JSON 字符串写入 MySQL JSON 列，读取时由 _decode 还原
    dao.upsert_summary(
        lead_id,
        json.dumps(tags, ensure_ascii=False),
        summary,
        analysis,
        lessons,
    )
    logger.info("生成项目总结 lead_id=%s tags=%s", lead_id, len(tags))
    return get_detail(lead_id)
