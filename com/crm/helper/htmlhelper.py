"""招标公告爬取工具。

注意：列表和正文的选择器是为合肥公共资源交易中心（ggzy.hefei.gov.cn）
硬编码的，换站点需要同步修改选择器。全程同步请求，没有重试；
出错时只 print，调用方通过空列表/空字符串判断失败。
"""
import requests
import time
import random
from bs4 import BeautifulSoup
from typing import List, Dict


def fetch_and_extract_tender_list(url: str, base_domain: str = None) -> List[Dict]:
    """抓取列表页，返回 [{title, url, date}]。

    href 以 / 开头时拼接 base_domain，其他相对路径保持原样。
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    result_list = []
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")

        # 合肥公共资源交易中心列表页结构；换站点必须改这里
        li_items = soup.select("ul.ewb-right-item > li.ewb-right-list.clearfix")
        print(f"列表页找到li数量：{len(li_items)}")
        for li in li_items:
            a_tag = li.select_one("a.l")
            date_tag = li.select_one("span.ewb-right-date.r")
            if not a_tag or not date_tag:
                continue

            title = a_tag.get("title", "").strip()
            href = a_tag.get("href", "").strip()
            pub_date = date_tag.get_text(strip=True)

            # 只处理以 / 开头的站内绝对路径，其他相对路径不做拼接
            if base_domain and href.startswith("/"):
                full_url = base_domain + href
            else:
                full_url = href

            result_list.append({
                "title": title,
                "url": full_url,
                "date": pub_date
            })
    except requests.exceptions.RequestException as e:
        print(f"列表页请求异常：{e}")
    return result_list


def extract_tender_detail(detail_url: str) -> str:
    """抓取详情页正文：优先 div.ewb-article，取不到则退回整页文本。"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(detail_url, headers=headers, timeout=15)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        # 这里是合肥公共资源交易中心正文div，优先精准提取
        content_tag = soup.select_one("div.ewb-article")
        if content_tag:
            content = content_tag.get_text(strip=True, separator="\n")
        else:
            content = soup.get_text(strip=True)
        return content
    except Exception as e:
        print(f"详情页 {detail_url} 解析失败：{e}")
        return ""


def run_all_tender_crawl(list_url: str, base_domain: str) -> List[Dict]:
    """总入口：抓列表 + 逐条抓详情 + 每条之后随机休眠 2~10 秒。

    串行执行，列表页有多少条就请求多少次，整页可能耗时数分钟。
    返回 [{title, url, date, content}]。
    """
    tender_list = fetch_and_extract_tender_list(list_url, base_domain)
    print(f"共获取到 {len(tender_list)} 条公告，开始遍历详情页\n")
    all_data = []
    for idx, item in enumerate(tender_list, start=1):
        title = item["title"]
        detail_url = item["url"]
        pub_date = item["date"]
        print(f"【{idx}/{len(tender_list)}】正在访问：{title}")

        # 调用封装好的详情提取函数
        detail_content = extract_tender_detail(detail_url)
        all_data.append({
            "title": title,
            "url": detail_url,
            "date": pub_date,
            "content": detail_content
        })

        # 礼貌限速，避免高频请求目标站；最后一条之后也会休眠
        sleep_sec = random.randint(2, 10)
        print(f"休眠 {sleep_sec} 秒...\n")
        time.sleep(sleep_sec)
    return all_data


if __name__ == "__main__":
    list_url = "https://ggzy.hefei.gov.cn/jyxx/002002/002002001/2.html"
    base_domain = "https://ggzy.hefei.gov.cn"
    result_data = run_all_tender_crawl(list_url, base_domain)
    # print(result_data)
    print("\n===== 全部抓取完成 =====")
    for d in result_data:
        print(f"标题：{d['title']}")
        print(f"链接：{d['url']}")
        print(f"日期：{d['date']}")
        print(f"内容：{d['content'][50]}...")
        print("-" * 60)

