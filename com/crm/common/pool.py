# -*- coding: utf-8 -*-
"""
数据库连接池（集中管理数据库连接配置 + 连接池）

为什么要用池：pymysql 的连接**不是线程安全的**，同一时刻只能被一个线程使用。
FastAPI 会把同步接口丢进线程池执行，多个请求并发时若共享一个连接，
轻则报 "Packet sequence number wrong"，重则 A 请求读到 B 请求的数据。

连接池保证每个请求拿到的是独占连接，用完归还，而不是每次重新握手
（TCP + 认证 + 权限加载约 1~5ms，白白浪费）。
"""
import os
from pathlib import Path

import pymysql
from dbutils.pooled_db import PooledDB
from dotenv import load_dotenv

# 项目根目录：pool.py -> common -> crm -> com -> 项目根
PROJECT_ROOT = Path(__file__).resolve().parents[3]
# override=False：真实环境变量优先，只有未设置时才用 .env
load_dotenv(PROJECT_ROOT / ".env", override=False)


def _env_int(name: str, default: int) -> int:
    """读取整数环境变量，非法值回退默认值。"""
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


# ============ 数据库连接配置（通过 .env / 环境变量覆盖）============
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),          # 数据库地址内网IP
    "port": _env_int("DB_PORT", 3306),                  # 端口号
    "user": os.getenv("DB_USER", "root"),               # 用户名
    "password": os.getenv("DB_PASSWORD", "123456"),     # 密码
    "database": os.getenv("DB_NAME", "school_db_study"),  # 数据库名
    "charset": "utf8mb4",                               # 字符编码
    "cursorclass": pymysql.cursors.DictCursor,          # 结果以字典返回
}

_pool = PooledDB(
    creator=pymysql,
    mincached=5,         # 启动时预先建好的空闲连接数
    maxcached=5,         # 空闲连接数上限，超出的会被真正关闭
    maxconnections=40,   # 同时活跃的连接上限，必须 ≥ FastAPI 线程池大小（默认 40），池子小了请求会排队等连接
    blocking=True,       # 池满时阻塞等待，而不是直接抛异常
    ping=1,              # 每次借出前 ping 一下，自动重连被 MySQL 断掉的空闲连接
    **DB_CONFIG,         # host/port/user/.../cursorclass
)

def get_conn():
    """
    借一个连接。用完必须 close() —— 对池化连接来说 close() 是**归还**，不是真关闭。
    """
    return _pool.connection()
