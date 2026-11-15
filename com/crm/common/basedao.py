# -*- coding: utf-8 -*-
"""
通用数据访问函数（BaseDao）

dao 层的查询多是「一进一出」的短操作，用这几个函数比拼装 cursor 更简洁。
池化连接支持 with 语法，块结束时 __exit__ 会把连接归还给池子。

执行方式分两种，自动判断，dao 层无感知：
- 不在事务中（current_conn() 返回 None）：维持历史行为——读借连接即还，
  写自动 commit 后归还。存量单步写（登录、改密码等）不受影响。
- 在事务中（service 层包了 `with tx():`）：直接用事务连接执行，
  不 commit 不归还，提交/回滚统一由 tx() 管。注意事务中的**读**也必须走
  事务连接，否则读不到同一事务里未提交的写入。
"""
from com.crm.common.db import current_conn
from com.crm.common.pool import get_conn


def query_one(sql, args=None):
    """只读：查一条，没有则返回 None。"""
    conn = current_conn()
    if conn is not None:
        # 事务中：用事务连接执行，不提交不归还
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()
    # 只读不需要事务，用 with 借连接、块结束自动归还，不必显式 close
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()


def query_all(sql, args=None):
    """只读：查多条，返回字典列表。"""
    conn = current_conn()
    if conn is not None:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()


def execute(sql, args=None):
    """写入：增/删/改，返回影响行数。

    事务中不提交（由 tx() 统一提交）；事务外维持旧行为自动提交。
    """
    conn = current_conn()
    if conn is not None:
        with conn.cursor() as cur:
            return cur.execute(sql, args)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            n = cur.execute(sql, args)
        conn.commit()            # 执行成功 → 提交事务，数据才真正落库
        return n
    except Exception:
        conn.rollback()          # ① 回滚：撤销本次未提交的写入，避免留下半截脏数据
        raise                    # ② 重新抛出：把异常上报给上层调用方，绝不「吞异常」
                                 #    若不写 raise，异常会被 except 吃掉、函数会隐式返回 None，
                                 #    调用方会误以为写入成功 —— 这就是最难排查的「静默失败」
    finally:
        conn.close()             # ③ 归还连接：无论成功还是异常都执行（close 是归还，不是真关闭）


def insert(sql, args=None):
    """写入：插入并返回新行的自增主键。提交时机同 execute。"""
    conn = current_conn()
    if conn is not None:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.lastrowid

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            new_id = cur.lastrowid   # 取本次 INSERT 生成的自增主键
        conn.commit()                # 提交后数据才真正落库
        return new_id
    except Exception:
        conn.rollback()          # ① 回滚：撤销本次未提交的插入，避免脏数据
        raise                    # ② 重新抛出：把异常上报给上层，不吞异常（否则调用方误判成功）
    finally:
        conn.close()             # ③ 归还连接：无论成功还是异常都执行
