"""项目总结提示词：标签、摘要、项目分析、经验总结。"""
from langchain_core.prompts import ChatPromptTemplate

SYSTEM = (
    "你是项目分析助手。只依据下面提供的项目资料回答，不要编造资料中没有的信息。"
    "使用中文，简洁清晰。"
)

tags_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        SYSTEM + "从项目资料中提取 3~6 个关键词标签，用中文逗号分隔，只输出标签。",
    ),
    ("human", "{context}"),
])

summary_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        SYSTEM + "用 150 字以内总结该项目的客户、内容、预算、进展等关键信息。",
    ),
    ("human", "{context}"),
])

analysis_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        SYSTEM + "分析该项目的商机机会、主要风险、竞争情况和推进建议，200 字以内。",
    ),
    ("human", "{context}"),
])

lessons_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        SYSTEM + "总结该项目在跟进、招投标、立项过程中的经验与教训，150 字以内。",
    ),
    ("human", "{context}"),
])
