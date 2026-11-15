"""
全局配置：项目路径 + 登录会话 + 日志
"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv

# ============ 项目路径 ============
# config.py -> common -> crm -> com -> 项目根
PROJECT_ROOT = Path(__file__).resolve().parents[3]
STATIC_DIR = PROJECT_ROOT / "static"
load_dotenv(PROJECT_ROOT / ".env", override=False)

# ============ 登录会话 ============
# 生产环境务必在 .env 中设置随机值
SESSION_SECRET = os.getenv("SESSION_SECRET", "aicrm-dev-session-secret-change-me")
SESSION_MAX_AGE = 7 * 24 * 60 * 60   # 7 天

# ============ 全局日志配置 ============
# 按天滚动：当天写 log/aicrm.log，跨天自动改名为 aicrm-YYYY-MM-DD.log
LOG_DIR = PROJECT_ROOT / "log"
LOG_DIR.mkdir(exist_ok=True)
file_handler = TimedRotatingFileHandler(
    LOG_DIR / "aicrm.log",
    when="midnight",
    interval=1,
    backupCount=30,          # 保留最近 30 天
    encoding="utf-8",
)
# 默认滚动名为 aicrm.log.2026-11-12，这里改成 aicrm-2026-11-12.log
file_handler.namer = lambda name: name.replace(".log.", "-") + ".log"

logging.basicConfig(
    level=logging.INFO,  # 配置日志输出级别
    # asctime:时间戳；threadName:当前运行的线程名称；levelname:日志输出级别；name:模块名称；message:日志信息
    format="%(asctime)s - %(threadName)s - [%(levelname)s] - %(name)s:%(message)s",  # 配置日志输出格式
    handlers=[
        file_handler,        # 文件日志（按天滚动）
        logging.StreamHandler(),  # 控制台输出
    ],
)
