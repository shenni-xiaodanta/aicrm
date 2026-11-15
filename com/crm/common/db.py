# -*- coding: utf-8 -*-
"""
事务上下文管理

为什么要单独做这一层：原项目 dao 层的 execute/insert 每次调用各自 commit，
「改负责人 + 写变更记录」这类两步写一旦中途失败，库里就留下只做了一半的数据
（owner/service.py 旧 docstring 自己承认了这一点）。

设计：用 contextvars 保存「当前请求绑定的事务连接」，
basedao 的读写函数优先取这个连接，dao 层函数签名完全不用改——
service 里把两次 dao 调用包进 `with tx():` 就自动进同一事务。

用法（service 层）::

    from com.crm.common.db import tx

    with tx():
        dao.update_owner(lead_id, owner_id)   # 走事务连接，不单独提交
        dao.insert_change(...)                # 同一连接、同一事务
    # 正常离开 with → 统一 commit；抛异常 → 统一 rollback
"""
import logging
from contextlib import contextmanager
from contextvars import ContextVar

from com.crm.common.pool import get_conn

logger = logging.getLogger(__name__)

# contextvars 而不是全局变量：FastAPI 把同步接口丢进线程池并发执行，
# 全局变量会让 A 请求的事务连接被 B 请求拿到（连接不是线程安全的）。
# contextvar 按执行上下文隔离，async/线程池下都安全。
_tx_conn: ContextVar = ContextVar("tx_conn", default=None)


def current_conn():
    """返回当前上下文绑定的事务连接；不在事务中时返回 None。

    basedao 的读写函数先调这里：非 None 就直接用事务连接
    （事务中的读必须走同一连接，否则读不到未提交的写入），提交/归还由 tx() 统一负责。
    """
    return _tx_conn.get()


@contextmanager
def tx():
    """写事务上下文：块内所有写入共享一个连接，成功统一提交，异常统一回滚。

    注意：
    - 不可重入：嵌套 tx() 直接抛 RuntimeError。内层 commit 会把外层
      未完成逻辑一起提交，回滚也无法整体撤销——所以从一开始就禁止嵌套，
      出现嵌套说明调用边界画错了，要在编码期暴露而不是运行期埋雷。
    - 事务期间禁止再调 common.llm / 高德这类慢外部调用：连接会被占住，
      池子（maxconnections=40）很容易被打满。先把外部调用做完，再进事务落库。
    """
    if _tx_conn.get() is not None:
        raise RuntimeError("tx() 不可嵌套调用：上一事务尚未结束时又开启了新事务")

    conn = get_conn()
    token = _tx_conn.set(conn)
    try:
        yield conn
        conn.commit()            # 全部 dao 调用成功 → 统一提交
    except Exception:
        conn.rollback()          # 任意一步失败 → 整体回滚，不留半截数据
        raise                    # 重新抛出，让上层照常走 api 层的异常分发
    finally:
        # 先复位上下文再归还连接：保证归还动作本身不会让别人误用这个连接
        _tx_conn.reset(token)
        conn.close()             # close 是归还给池子，不是真关闭
