"""站点模板结构与合法性校验：全项目唯一的一份 schema。

探测（probe.py）产出的模板、人工改配方（crawl/api.py 的 PUT /sites/{id}）
都从这里过校验——两处消费、一份定义，禁止在调用方各自手写规则。
模板结构 = crm_crawl_site 表 selectors / pagination 两个 JSON 列的内容：

selectors = {
    "list_item":      "ul.ewb-right-item > li.ewb-right-list.clearfix",
    "list_link":      "a.l",
    "title_attr":     "title",          # 完整标题所在属性名；没有则 ""
    "list_date":      "span.ewb-right-date.r",
    "detail_content": ["div.ewb-info-bd", "div.ewb-article"],   # 候选数组，按序尝试
}
pagination = {
    "mode": "page_param",
    "url_template": "https://.../{page}.html",
    "start_page": 2,                   # 合肥怪癖：第 1 页 404
    "step": 1,
}
"""


def validate_template(template):
    """校验一份站点模板 dict，不合法抛 ValueError（message 面向用户可读）。

    只做「结构 + 非空」级别的校验；选择器语法对不对、页面里能不能
    命中，属于真页面回验的职责（probe.py / 采集时的 parse_list），
    这里不重复——两层分开，报错才能定位到「格式错」还是「选不中」。
    """
    if not isinstance(template, dict):
        raise ValueError("站点模板必须是一个对象")

    selectors = template.get("selectors")
    if not isinstance(selectors, dict):
        raise ValueError("selectors 必须是对象")
    for key in ("list_item", "list_link"):
        value = selectors.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"selectors.{key} 不能为空")
    detail = selectors.get("detail_content")
    if (
        not isinstance(detail, list)
        or not detail
        or not all(isinstance(sel, str) and sel.strip() for sel in detail)
    ):
        raise ValueError("selectors.detail_content 必须是非空字符串数组")

    pagination = template.get("pagination")
    if not isinstance(pagination, dict):
        raise ValueError("pagination 必须是对象")
    if (pagination.get("mode") or "").strip() != "page_param":
        raise ValueError("pagination.mode 目前只支持 page_param")
    url_template = (pagination.get("url_template") or "").strip()
    if not url_template:
        raise ValueError("pagination.url_template 不能为空")
    if "{page}" not in url_template:
        raise ValueError("pagination.url_template 必须包含 {page} 占位符")
    try:
        start_page = int(pagination.get("start_page") or 1)
        step = int(pagination.get("step") or 1)
    except (TypeError, ValueError):
        raise ValueError("pagination.start_page / step 必须是整数")
    if start_page < 1:
        raise ValueError("pagination.start_page 不能小于 1")
    if step < 1:
        raise ValueError("pagination.step 不能小于 1")
