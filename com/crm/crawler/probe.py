"""LLM 站点探测：列表页出解析配方 → 详情页出正文容器 → 真页面回验。

探测只负责「算出模板 + 验证模板」，不碰数据库；入库由 crawl/service
在事务里完成（crawler 不懂业务）。任何一步不达标抛 ProbeError
（message 面向用户可读），绝不带着没验证过的模板悄悄入库——
这是 AR-A02 的硬要求：探测必须同时验证详情页正文能取到实质内容。

两段式的原因：正文容器只看列表页猜 class 名必然翻车（中国政府采购网
实测猜成「相关内容」侧栏），必须先抓一个真实详情页，把骨架喂给模型选。
所以探测 = 2 次 LLM 调用 + 4 次真实请求（列表 / 详情 / 下一页等）。

回验三关（全部真页面，不靠模型自评）：
① 列表：parse_list 至少解析出 3 条带链接的公告；
② 正文：候选选择器在详情页取到 ≥300 字且命中公告关键词；
③ 翻页：url_template 生成的下一页必须可访问且能解析出公告。
"""
import logging
import re

from bs4 import BeautifulSoup, Comment
from pydantic import BaseModel

from com.crm.common.llm import llm
from com.crm.crawler.fetcher import FetchError, get as fetch
from com.crm.crawler.paginator import build_page_url
from com.crm.crawler.parser import MIN_DETAIL_LEN, parse_list
from com.crm.crawler.prompts import detail_prompt, probe_prompt
from com.crm.crawler.template import validate_template
from com.crm.helper.texthelper import clip
from com.crm.helper.urlhelper import origin

logger = logging.getLogger(__name__)

# 骨架喂给模型前压缩到这个字符数：政务列表页 DOM 很深，全量给会
# 把上下文撑爆且噪声大；只留带 id/class 的元素 + 链接 + 分页提示
SKELETON_MAX_CHARS = 12000

# 列表回验阈值：公告列表一页通常 10~20 条，少于 3 条说明选择器
# 选中的大概率是导航或推荐位，不是公告列表本身
MIN_LIST_ITEMS = 3

# 正文回验：第 1 个详情页参与「选容器 + 验证」（模型看的就是它），
# 第 2 个只做旁证——候选选择器在第 2 页也该取到正文，否则说明
# 选中的是第 1 页独有的结构。第 2 页失败只记警告不判死（不同类型
# 公告版式会有差异，采集期还有 parse_list / extract_detail 兜底）。
DETAIL_SAMPLES = 2

# 正文关键词（AR-A02）：命中任意一个即认为抓到的是公告主体
# 而不是导航壳。中标/成交类公告没有"预算"，所以补两个结果词。
CONTENT_KEYWORDS = ("预算", "采购人", "项目编号", "招标人", "中标", "成交")

# 疑似分页链接的 href 特征：/2.html 这类页码后缀，或 page= 系查询串。
# 只用来给模型提示，真正的翻页规律以模型输出的 url_template 为准
_PAGE_HREF_RE = re.compile(
    r"(?:/\d{1,3}\.html|[?&](?:page|pageno|pageindex|pager|currentpage)=\d{1,3})",
    re.I,
)


class ProbeError(Exception):
    """探测失败（模型输出不合法 / 回验不过），message 面向用户可读。"""


# deepseek-flash 不支持强制 tool_choice，与商机抽取同款走 json_mode
class _ListProbeOutput(BaseModel):
    list_item: str
    list_link: str
    title_attr: str = ""
    list_date: str = ""
    url_template: str
    start_page: int = 1
    step: int = 1
    site_name: str = ""


class _DetailProbeOutput(BaseModel):
    detail_content: list[str]


probe_chain = probe_prompt | llm.with_structured_output(_ListProbeOutput, method="json_mode")
detail_chain = detail_prompt | llm.with_structured_output(_DetailProbeOutput, method="json_mode")


# ---------------------------------------------------------------------
# 页面骨架压缩（只读纯函数）
# ---------------------------------------------------------------------
def skeleton(html, max_chars=SKELETON_MAX_CHARS):
    """把整页 HTML 压成只含结构信息的骨架文本。

    保留：带 id/class 的元素、a/li/tr/td/th/ul/table/p 元素
    （p 不带 class 但正文段落全在它里面，详情页选正文容器靠它）。
    丢弃：script/style 等噪声标签、注释、无属性又无文本的空壳层。
    锚点保留 href 与文本（模型推导 list_link / url_template 全靠它）。
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "link", "meta"]):
        tag.decompose()
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    lines = []
    for tag in soup.find_all(True):
        classes = " ".join(tag.get("class") or [])
        keep = (
            tag.name in ("a", "li", "tr", "td", "th", "ul", "table", "p")
            or tag.get("id")
            or classes
        )
        if not keep:
            continue
        # 缩进表达层级，压到 40 层封顶防止深 DOM 把行撑爆
        depth = min(len(list(tag.parents)), 40)
        parts = ["  " * depth, f"<{tag.name}"]
        if tag.get("id"):
            parts.append(f' id="{tag["id"]}"')
        if classes:
            parts.append(f' class="{classes}"')
        if tag.name == "a":
            href = (tag.get("href") or "").strip()
            if href:
                parts.append(f' href="{clip(href, 200)}"')
            parts.append(f">{clip(tag.get_text(' ', strip=True), 80)}</a>")
        else:
            # 只取直接文本，不递归——子元素自己会输出一行
            own = tag.find(string=True, recursive=False)
            if own and own.strip():
                parts.append(f">{clip(own.strip(), 60)}")
            parts.append(">")
        lines.append("".join(parts))

    return "\n".join(lines)[:max_chars]


def pagination_hints(html, limit=20):
    """从页面里捞出疑似翻页的链接，供模型推导 url_template。

    这是 AR-A01「翻页规则不得靠猜 URL 数字规律」的探测侧落点：
    模型优先从这里真实存在的翻页地址推导模板，而不是瞎猜。
    """
    soup = BeautifulSoup(html, "html.parser")
    seen, hints = set(), []
    for a in soup.find_all("a", href=_PAGE_HREF_RE):
        href = (a.get("href") or "").strip()
        if not href or href in seen:
            continue
        seen.add(href)
        text = clip(a.get_text(" ", strip=True), 20)
        hints.append(f"[{text}]({href})")
        if len(hints) >= limit:
            break
    return "\n".join(hints) if hints else "（页面上没有发现疑似翻页链接）"


# ---------------------------------------------------------------------
# 探测主流程
# ---------------------------------------------------------------------
def _strict_detail(html, candidates):
    """探测回验专用：按候选选择器取正文，**不做整页文本兜底**。

    parser.extract_detail 的兜底（全页 get_text）是采集期的降级策略，
    但在探测里「兜底成功」等于正文选择器根本没验证过——照单全收
    会把失效模板当成功入库。这里候选全不达标就返回 (None, 最长命中字数)。
    """
    soup = BeautifulSoup(html, "html.parser")
    best_len = 0
    for sel in candidates or []:
        tag = soup.select_one(sel)
        if not tag:
            continue
        content = tag.get_text(strip=True, separator="\n")
        best_len = max(best_len, len(content))
        if len(content) >= MIN_DETAIL_LEN:
            return content, sel
    return None, best_len


def _invoke_chain(chain, inputs, step):
    """包一层 LLM 调用：任何异常都转成带环节名的 ProbeError，
    不让 langchain 的内部报错（KeyError/Timeout...）裸奔给用户。"""
    try:
        return chain.invoke(inputs)
    except Exception as e:
        logger.warning("探测环节 [%s] 模型调用失败：%s", step, e)
        raise ProbeError(f"模型识别失败（{step}）：{clip(str(e), 200)}")


def _list_fail_reason(list_html, selectors, parsed_count):
    """列表回验失败时按「选择器命中情况」给分级原因。

    - 0 命中：原始 HTML 里根本没有这个结构 → 大概率 JS 注入列表
    - 命中了但捞不到带链接的公告：容器在原始 HTML 里是空壳
      （AJAX 先插容器再填数据，如合肥新站的 #ajaxHtml），或链接
      选择器配错
    分级的意义：让用户不用 Ctrl+U 也能判断该换站点还是该调选择器。
    """
    item_sel = selectors["list_item"]
    prefix = (
        f"列表项选择器回验失败：[{item_sel}] "
        f"只解析到 {parsed_count} 条带链接的公告（要求 ≥ {MIN_LIST_ITEMS}）。"
    )
    try:
        matched = len(BeautifulSoup(list_html, "html.parser").select(item_sel))
    except Exception:
        matched = -1
    if matched == 0:
        return (prefix
                + "该选择器在原始 HTML 里一个元素都没命中——浏览器里看到的列表"
                "大概率是 JS 动态注入的（浏览器渲染类站点），本期 HTTP 直连不支持，"
                "请换一个服务端渲染的列表页")
    if matched > 0:
        return (prefix
                + f"但选择器在原始 HTML 里命中了 {matched} 个元素——容器存在却"
                "捞不到带链接的公告，说明列表数据是先插空容器再由 AJAX 填充"
                "（浏览器渲染类站点），本期 HTTP 直连不支持，请换一个服务端渲染的列表页")
    return (prefix + "如果该页面在浏览器里能看到列表，大概率是列表数据由 JS 动态加载，"
            "本期 HTTP 直连不支持")


def run_probe(list_url, interval=2.0):
    """对入口列表页执行探测，返回 (template, evidence)。

    template 结构即 crm_crawl_site 的 selectors + pagination（外加
    site_name 建议），入库前由 template.validate_template 把最后一道关。
    evidence 是回验证据包：解析到几条、正文命中哪个选择器、下一页
    地址等，供前端展示「探测到了什么」，也供验收时人工比对。
    FetchError / ProbeError 由调用方转成可读文案。
    """
    # url 拼接基准必须用完整入口页 URL 而不是裸域名：ccgp 实测踩坑，
    # 详情链接是相对路径（202611/t...htm），拿域名当基准会把列表页
    # 自身的目录路径（/cggg/zygg/gkzb/）丢掉，拼出打不开的 404 地址
    list_html = fetch(list_url)  # FetchError 直接上抛，信息已可读

    # ---- 第一段：列表页 → 选择器 + 翻页模板 ----
    result = _invoke_chain(probe_chain, {
        "list_url": list_url,
        "skeleton": skeleton(list_html),
        "page_hints": pagination_hints(list_html),
    }, "列表页结构")

    selectors = {
        "list_item": result.list_item.strip(),
        "list_link": result.list_link.strip(),
        "title_attr": (result.title_attr or "").strip(),
        "list_date": (result.list_date or "").strip(),
        "detail_content": [],   # 详情容器在第二段探测后补全
    }
    pagination = {
        "mode": "page_param",
        "url_template": result.url_template.strip(),
        "start_page": max(1, int(result.start_page or 1)),
        "step": max(1, int(result.step or 1)),
    }

    # ---- 回验① 列表：选择器必须在真页面解析出足够的公告 ----
    items = [item for item in parse_list(list_html, selectors, list_url) if item["url"]]
    if len(items) < MIN_LIST_ITEMS:
        raise ProbeError(
            f"列表项选择器回验失败：[{selectors['list_item']}] "
            f"只解析到 {len(items)} 条带链接的公告（要求 ≥ {MIN_LIST_ITEMS}）。"
            "如果该页面在浏览器里能看到列表，大概率是列表数据由 JS 动态加载"
            "（浏览器渲染类站点），本期 HTTP 直连不支持，请换一个服务端渲染的列表页"
        )

    # ---- 第二段：真实详情页 → 正文容器候选 ----
    detail_html = None
    detail_url = ""
    attempts = []  # 失败要带出真实原因，不能只说「无法访问」
    for item in items[:DETAIL_SAMPLES]:
        try:
            detail_html = fetch(item["url"], interval=interval, referer=list_url)
            detail_url = item["url"]
            break
        except FetchError as e:
            attempts.append(f"{item['url']}（{clip(str(e), 100)}）")
            continue
    if detail_html is None:
        raise ProbeError(
            "详情页下载失败，已尝试：" + "；".join(attempts)
            + "。如果这些地址在浏览器里能打开，大概率是站点反爬拦截（可稍后重试）"
        )

    detail_result = _invoke_chain(detail_chain, {
        "detail_url": detail_url,
        "skeleton": skeleton(detail_html),
    }, "详情页正文容器")
    selectors["detail_content"] = [
        sel.strip() for sel in (detail_result.detail_content or []) if sel.strip()
    ]
    if not selectors["detail_content"]:
        raise ProbeError("模型没有给出正文容器候选，请重试或人工配置选择器")

    # ---- 回验② 正文：候选必须在「模型看过的那页」上取到实质内容 ----
    content, sel = _strict_detail(detail_html, selectors["detail_content"])
    if content is None:
        raise ProbeError(
            "正文选择器未定位：模型给出的候选 {} 在详情页上取不到 ≥{} 字的正文".format(
                selectors["detail_content"], MIN_DETAIL_LEN
            )
        )
    hits = [k for k in CONTENT_KEYWORDS if k in content]
    if not hits:
        raise ProbeError(
            "正文选择器未定位：选中的容器取到了 {} 字内容，但不含公告关键词"
            "（{}），可能抓到的是导航壳或推荐位".format(
                len(content), "/".join(CONTENT_KEYWORDS)
            )
        )
    evidence_detail = {
        "url": detail_url, "selector": sel,
        "chars": len(content), "keywords": hits,
    }

    # 旁证：第 2 个详情页也用同一组候选试一次（可访问的话）
    warning = ""
    if len(items) > 1:
        try:
            html2 = fetch(items[1]["url"], interval=interval, referer=list_url)
            content2, _ = _strict_detail(html2, selectors["detail_content"])
            if content2 is None:
                warning = "第 2 个详情页用同组候选取不到正文，选择器可能只适配部分版式"
        except FetchError:
            pass

    # ---- 回验③ 翻页：下一页必须可访问且能解析出公告 ----
    next_page_no = pagination["start_page"] + pagination["step"]
    try:
        next_page_url = build_page_url(pagination, list_url, next_page_no)
        next_html = fetch(next_page_url, interval=interval, referer=list_url)
        next_items = [
            item for item in parse_list(next_html, selectors, list_url)
            if item["url"]
        ]
    except (FetchError, ValueError) as e:
        raise ProbeError(
            f"翻页模板回验失败：第 {next_page_no} 页访问或解析失败"
            f"（{clip(str(e), 120)}），url_template 可能不是该站的真实翻页规律"
        )
    if not next_items:
        raise ProbeError(
            f"翻页模板回验失败：第 {next_page_no} 页（{next_page_url}）"
            "解析到 0 条公告，url_template 可能不是该站的真实翻页规律"
        )

    template = {
        "selectors": selectors,
        "pagination": pagination,
        "site_name": (result.site_name or "").strip(),
    }
    try:
        validate_template(template)
    except ValueError as e:
        raise ProbeError(f"模型输出的模板不合法：{e}")

    evidence = {
        "list_items": len(items),
        "sample_titles": [clip(item["title"], 40) for item in items[:3]],
        "detail": evidence_detail,
        "warning": warning,
        "next_page_url": next_page_url,
        "next_page_items": len(next_items),
    }
    logger.info(
        "站点探测成功 url=%s items=%s detail=%s(%s字) next=%s(%s条)%s",
        list_url, len(items), evidence_detail["selector"],
        evidence_detail["chars"], next_page_url, len(next_items),
        f"（警告：{warning}）" if warning else "",
    )
    return template, evidence
