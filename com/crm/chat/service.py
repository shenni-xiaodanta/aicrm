"""概况聊天业务层：组装项目知识库、多轮消息、流式回答。"""
import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from com.crm.chat import dao
from com.crm.common.exceptions import BizException
from com.crm.common.llm import llm
from com.crm.helper.projectcontext import build_project_context

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是“概况”助手。只能依据下面提供的项目资料回答用户问题。"
    "资料没有的信息不要编造；资料不足时请明确说明。回答简洁，使用中文。"
)
# 送给模型的历史消息上限，避免上下文过长；接口展示最多 50 条
HISTORY_LIMIT = 20


def build_messages(lead_id, user_id, question):
    """组装系统提示 + 项目知识库 + 当前用户历史 + 本次提问。

    历史只查 lead_id + user_id，保证同一项目下不同用户的聊天互相隔离；
    项目资料本身由 build_project_context 按 lead_id 读取，所有用户共享。
    """
    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT + "\n\n" + build_project_context(lead_id)
        )
    ]
    for item in dao.list_history(lead_id, user_id, limit=HISTORY_LIMIT):
        if item["role"] == "user":
            messages.append(HumanMessage(content=item["content"]))
        else:
            messages.append(AIMessage(content=item["content"]))
    messages.append(HumanMessage(content=question))
    return messages


def save_message(lead_id, user_id, role, content):
    return dao.insert_message(lead_id, user_id, role, content)


def list_history(lead_id, user_id):
    """当前用户在该项目下的聊天历史（界面最多展示 50 条）。"""
    if int(lead_id) <= 0:
        raise BizException("商机ID无效", code=1000)
    return dao.list_history(int(lead_id), user_id, limit=50)


def stream_reply(lead_id, user_id, messages):
    """生成器：流式返回模型文本，结束后保存完整回答。

    - 正常结束：把 parts 拼接后作为 assistant 消息落库
    - 模型异常：先 yield 一段中断提示，再把已生成的部分保存下来
    - 客户端断开：生成器被关闭，finally 仍会执行
    """
    parts = []
    try:
        for chunk in llm.stream(messages):
            text = chunk.content if isinstance(chunk.content, str) else ""
            if text:
                parts.append(text)
                yield text
    except Exception as exc:
        logger.exception("聊天流式输出失败 lead_id=%s user_id=%s", lead_id, user_id)
        yield "\n[回答中断：" + str(exc) + "]"
    finally:
        if parts:
            save_message(lead_id, user_id, "assistant", "".join(parts))
