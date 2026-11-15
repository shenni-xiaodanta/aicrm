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
    """抓取详情页正文：按候选选择器依次尝试，全部取不到实质内容才退回整页文本。

    注意：站点改版会让选择器失效，且失效是「静默」的——2026-11 实测合肥站
    正文容器已从 div.ewb-article 改名为 div.ewb-info-bd，旧代码拿整页文本
    （含导航栏、开标倒计时等噪声）喂给 LLM，抽取质量被拉低且无任何报错。
    所以除了多候选兜底，还必须对取到的内容做长度校验：少于 MIN_CONTENT_LEN
    视为「没取到正文」，继续尝试下一候选，而不是直接采信。
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    # 候选顺序即优先级：ewb-info-bd 是合肥站当前真实容器（实测 1370 字），
    # ewb-article 是旧版容器，留作兼容尚未改版的同构站点
    CONTENT_SELECTORS = [
        "div.ewb-info-bd",
        "div.ewb-article",
    ]
    MIN_CONTENT_LEN = 300  # 正文低于此长度基本是导航/页头，不当成有效正文

    try:
        resp = requests.get(detail_url, headers=headers, timeout=15)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        for selector in CONTENT_SELECTORS:
            content_tag = soup.select_one(selector)
            if not content_tag:
                continue
            content = content_tag.get_text(strip=True, separator="\n")
            if len(content) >= MIN_CONTENT_LEN:
                return content
            # 命中了但内容太短（可能是改版后的空壳容器），不采信，试下一个
            print(f"详情页 {detail_url} 选择器 {selector} 仅取到 {len(content)} 字，不足 {MIN_CONTENT_LEN}，尝试下一候选")
        # 全部候选都取不到实质内容：退回整页文本（带噪声，但好过空串）
        return soup.get_text(strip=True)
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

