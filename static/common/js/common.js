/* 共用工具函数。
 * 约定：后端业务失败通常返回 HTTP 200 + body.code（例如 code=401）。
 * request 只在 HTTP 非 2xx 时抛异常，业务错误需要调用方检查 res.code。
 */
window.App = {
  /* HTML 转义：适用于元素文本和属性值；null/undefined 转空串 */
  esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  },

  /* 通用 JSON 请求：data 存在时序列化并设置 Content-Type；HTTP 非 2xx 抛错 */
  async request(url, method = "GET", data) {
    const options = { method, headers: {} };
    if (data !== undefined) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(data);
    }
    const res = await fetch(url, options);
    if (!res.ok) throw new Error("HTTP " + res.status);
    return res.json();
  },

  /* GET JSON */
  async fetchJson(url) {
    return window.App.request(url, "GET");
  },

  /* POST JSON */
  async postJson(url, data) {
    return window.App.request(url, "POST", data);
  },
};
