"""翻页器：按站点配方的 pagination JSON 生成各页 URL。

本期只支持 page_param 模式（URL 模板 + {page} 占位）；
xhr_api / page_offset 结构上预留，未实现的模式在这里直接报错，
让上层把「配方不支持」和「页面抓不到」区分开。
"""
from urllib.parse import urljoin


def build_page_url(pagination, base_url, page_no):
    """生成第 page_no 页的 URL。

    url_template 配完整地址（含 {page} 占位）；若只填了相对路径，
    用入口页 base_url 补全 scheme + 域名。
    """
    mode = (pagination.get("mode") or "").strip()
    if mode != "page_param":
        raise ValueError(f"暂不支持翻页模式：{mode or '(未配置)'}")

    template = (pagination.get("url_template") or "").strip()
    if not template:
        raise ValueError("站点配方缺少 pagination.url_template")
    if not template.startswith(("http://", "https://")):
        template = urljoin(base_url, template)
    return template.replace("{page}", str(page_no))


def iter_pages(pagination, base_url, max_pages):
    """按 start_page / step 依次产出 (url, page_no)，最多 max_pages 页。

    start_page 的存在是为合肥站的怪癖：第 1 页 404，最新内容从
    第 2 页开始——这是站点事实，写成配方数据而不是代码特判。
    """
    start = int(pagination.get("start_page") or 1)
    step = int(pagination.get("step") or 1)
    if step <= 0:
        step = 1
    page_no = start
    for _ in range(max(1, max_pages)):
        yield build_page_url(pagination, base_url, page_no), page_no
        page_no += step
