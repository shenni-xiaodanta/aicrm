"""全局大模型配置：所有业务模块统一从这里导入，不再各自维护。"""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

# override=False：真实环境变量优先，只有未设置时才用 .env
load_dotenv(override=False)

# 全局模型实例：各业务链共享，避免重复创建连接。
# 商机批量抽取、总结 RunnableParallel 会并发调用这个实例，模型客户端本身支持并发。
llm = init_chat_model(
    model=os.getenv("DEEPSEEK_MODEL_FLASH"),
    temperature=0.0,           # 信息提取要求稳定，关闭随机性
    top_p=0.5,                 # 缩小采样范围，减少无关输出
    max_tokens=3000,           # 商机抽取字段较多，预留足够输出长度
    frequency_penalty=0.0,     # 不做重复词惩罚
    reasoning_effort="none",   # 关闭深度思考，降低响应延迟
)
