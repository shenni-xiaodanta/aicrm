"""HTTP 下载器：重试、退避、编码处理。

与站点结构无关（结构归 parser），与业务无关（入库归 service）。
失败统一抛 FetchError，由调用方决定记失败明细还是终止任务——
这里绝不静默返回空串，那是旧 htmlhelper 掩盖「站点失效」的根源。
"""
import logging
import random
import time

import requests

logger = logging.getLogger(__name__)

# 部分站点对无 UA / 异常 UA 直接 403，伪装成常规浏览器
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


class FetchError(Exception):
    """下载最终失败（重试耗尽），message 面向用户可读。"""


def get(url, charset="utf-8", max_retry=2, interval=None, timeout=15):
    """下载页面并返回解码后的文本。

    - 重试：线性退避（2s/4s...）加随机抖动，避免把站点打疼
    - charset：站点配方指定编码；空串则用 apparent_encoding 自动猜
      （部分政务站声明编码与实际不符，直接信响应头会拿到乱码）
    - interval：本次请求前的礼貌性等待秒数（None=不等待），
      由调用方对每个请求传入，保证「同站串行 + 间隔随机」
    - 全部重试失败抛 FetchError，绝不静默返回空串
    """
    if interval:
        time.sleep(max(0.5, interval + random.uniform(-1, 1)))

    last_err = None
    for attempt in range(max_retry + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            resp.encoding = charset or resp.apparent_encoding
            return resp.text
        except requests.exceptions.RequestException as e:
            last_err = e
            if attempt < max_retry:
                # 重试前退避：第 1 次约 2s、第 2 次约 4s，各带 0~1s 抖动
                time.sleep((attempt + 1) * 2 + random.uniform(0, 1))
    raise FetchError(f"{type(last_err).__name__}: {last_err}")
