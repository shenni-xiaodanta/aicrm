# -*- coding: utf-8 -*-
"""列表页诊断脚本（只读，不写库不改库）。

用途：点采集后显示「列表页找到li数量： 0」时，跑本脚本看真实原因。
它会读取 crm_crawl_source 里配置的 list_url，真实请求一次，逐层报告：
HTTP 状态码 / 页面大小 / 编码 / 各候选选择器命中数 / 页面文本开头。

执行方式（在项目根目录）：
  .venv\\Scripts\\python.exe probe_list_page.py
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests
from bs4 import BeautifulSoup

from com.crm.common.pool import get_conn

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 与 htmlhelper 同款候选（新增一个兜底 li 级别，判断是容器没了还是 li 变了）
SELECTORS = [
    "ul.ewb-right-item > li.ewb-right-list.clearfix",
    "ul.ewb-right-item li",
    "li.ewb-right-list",
    "ul li a.l",
]


def main():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, province, city, list_url, base_domain "
                "FROM crm_crawl_source"
            )
            sources = cur.fetchall()

    if not sources:
        print("库里没有采集源配置")
        return

    for src in sources:
        print("=" * 70)
        print(f"采集源 #{src['id']} {src['province']}/{src['city']}")
        print(f"  list_url    = {src['list_url']}")
        print(f"  base_domain = {src['base_domain']}")

        try:
            resp = requests.get(src["list_url"], headers=HEADERS, timeout=15)
        except Exception as e:
            print(f"  [×] 请求失败：{type(e).__name__}: {e}")
            continue

        print(f"  HTTP 状态码 = {resp.status_code}（200 不代表是正常列表页，要看下面命中数）")
        print(f"  页面大小 = {len(resp.text)} 字符 · 疑似编码 = {resp.apparent_encoding}")

        soup = BeautifulSoup(resp.text, "html.parser")
        for sel in SELECTORS:
            print(f"  选择器命中 [{sel}] = {len(soup.select(sel))} 个")

        text = soup.get_text(strip=True)
        print(f"  页面可见文本共 {len(text)} 字，开头 200 字：")
        print("  | " + text[:200].replace("\n", " ¶ "))
        print()
        print("  判断参考：")
        print("  · 全部选择器 0 命中 + 文本很短/含『验证/安全/稍候』→ 大概率被拦截或要 JS 渲染")
        print("  · 全部 0 命中 + 文本正常 → list_url 指向的页面 DOM 结构不对（URL 配错了）")
        print("  · 第 2/3 个候选有命中、第 1 个没有 → 站点改版，li 的 class 变了")


if __name__ == "__main__":
    main()
