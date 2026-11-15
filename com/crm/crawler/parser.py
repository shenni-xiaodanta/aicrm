"""页面解析器：按站点配方的 selectors JSON 抽取列表项与详情正文。

纯函数纪律：只做 (html, 配方) → 数据，不发请求、不碰数据库。
所有选择器来自配方而不是本文件——全项目不允许出现站点专属
CSS 选择器硬编码（B0 后定下的硬验收），站点适配 = 新增一行配方数据。
"""
from urllib.parse import urljoin

from bs4 import BeautifulSoup

# 正文低于此长度视为「空壳/导航噪声」，不算有效正文。
# 与 htmlhelper 止血时定的阈值一致：2026-11 实测合肥站正文 1370 字，
# 而空壳容器只能捞出几十字的导航和页头。
MIN_DETAIL_LEN = 300


def parse_list(html, selectors, base_url):
    """解析列表页，返回 [{title, url, date}]。

    - href 以 / 开头拼 base_url 域名，其他相对路径用 urljoin 补全
    - 标题优先取 title_attr 指定的属性（合肥站在 a 的 title 属性里，
      标签文本是截断的），取不到再退回标签文本
    - 选择器缺 list_item / list_link 视为配方损坏，抛错而非返回空列表：
      「配方错了」和「页面没数据」必须区分
    """
    item_sel = selectors.get("list_item")
    link_sel = selectors.get("list_link")
    if not item_sel or not link_sel:
        raise ValueError("站点配方缺少 list_item / list_link")

    title_attr = (selectors.get("title_attr") or "").strip()
    date_sel = (selectors.get("list_date") or "").strip()

    soup = BeautifulSoup(html, "html.parser")
    out = []
    for item in soup.select(item_sel):
        a = item.select_one(link_sel)
        if not a:
            continue
        if title_attr:
            title = (a.get(title_attr) or "").strip()
        else:
            title = ""
        title = title or a.get_text(strip=True)

        href = (a.get("href") or "").strip()
        if not href:
            continue
        if href.startswith(("http://", "https://")):
            url = href
        else:
            url = urljoin(base_url, href)

        date = ""
        if date_sel:
            date_tag = item.select_one(date_sel)
            date = date_tag.get_text(strip=True) if date_tag else ""

        out.append({"title": title, "url": url, "date": date})
    return out


def extract_detail(html, candidate_selectors):
    """按候选选择器依次提取正文，全部不达标退回整页文本。

    命中但内容太短不采信（可能是改版后的空壳容器），继续试下一候选；
    每次降级都 print 留痕——这是旧 htmlhelper 踩过的坑：静默退化成
    整页文本会把导航噪声喂给 LLM，抽取质量被拉低还查不到原因。
    """
    soup = BeautifulSoup(html, "html.parser")
    for sel in candidate_selectors or []:
        tag = soup.select_one(sel)
        if not tag:
            continue
        content = tag.get_text(strip=True, separator="\n")
        if len(content) >= MIN_DETAIL_LEN:
            return content
        print(f"详情正文选择器 [{sel}] 仅取到 {len(content)} 字 "
              f"（不足 {MIN_DETAIL_LEN}），尝试下一候选")
    return soup.get_text(strip=True)
