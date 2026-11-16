# -*- coding: utf-8 -*-
"""站点探测验收脚本（只读，不写库不改库）。

用途：前端站点管理页没做之前，用命令行对任意列表页 URL 跑一次
完整的「LLM 探测 + 真页面回验」，打印配方与证据，验收两条硬指标：
  · 合肥站应探测出 detail_content 命中 div.ewb-info-bd（不是已失效的 div.ewb-article）
  · 探测失败时给出可读原因，而不是报 500
注意：探测会真实请求入口页 + 2 个详情页 + 下一页，并调用一次 DeepSeek。

执行方式（在项目根目录）：
  .venv\\Scripts\\python.exe probe_site.py <列表页URL>
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from com.crm.crawler.fetcher import FetchError
from com.crm.crawler.probe import ProbeError, run_probe


def main():
    if len(sys.argv) < 2:
        print("用法：python probe_site.py <列表页URL>")
        print("例如：python probe_site.py https://ggzyjy.hefei.gov.cn/jyxx/002002/002002001/2.html")
        sys.exit(1)

    url = sys.argv[1].strip()
    print(f"开始探测：{url}")
    print("（真实请求入口页、详情页、下一页 + 一次 DeepSeek 调用，约需 30~60 秒）\n")

    try:
        template, evidence = run_probe(url)
    except FetchError as e:
        print(f"[×] 探测失败：列表页下载失败：{e}")
        sys.exit(1)
    except ProbeError as e:
        print(f"[×] 探测失败：{e}")
        sys.exit(1)
    except Exception as e:
        # 非站点问题（代码缺陷/环境异常）：给一行可读结论 + 简短堆栈，
        # 避免把几十行 traceback 当成「站点探测失败」误导排查方向
        import traceback
        print(f"[!] 内部错误（非站点问题）：{type(e).__name__}: {e}")
        print("    以下堆栈供开发定位：")
        traceback.print_exc()
        sys.exit(2)

    print("[√] 探测成功，回验证据：")
    print(f"  列表解析          = {evidence['list_items']} 条公告")
    for title in evidence["sample_titles"]:
        print(f"    · {title}")
    detail = evidence["detail"]
    print(f"  正文选择器命中    = {detail['selector']}（{detail['chars']} 字）")
    print(f"  正文关键词        = {'/'.join(detail['keywords'])}")
    print(f"  详情样例          = {detail['url']}")
    print(f"  下一页回验        = {evidence['next_page_url']}（{evidence['next_page_items']} 条）")
    print("\n站点模板（写入 crm_crawl_site 的 selectors / pagination）：")
    print(json.dumps(
        {"selectors": template["selectors"], "pagination": template["pagination"]},
        ensure_ascii=False, indent=2,
    ))


if __name__ == "__main__":
    main()
