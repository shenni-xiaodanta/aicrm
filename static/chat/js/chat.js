/* 概况：多轮聊天 + 流式输出。
 * 由 map.js 在每次点击水滴、打开 InfoWindow 后调用 ChatPage.init(lead_id)。
 */
(function () {
  "use strict";

  function pane() {
    return document.getElementById("iwChat");
  }

  function scrollBottom(box) {
    box.scrollTop = box.scrollHeight;
  }

  // 用 textContent 写入，避免模型输出被当成 HTML 执行
  function appendMessage(el, role, content) {
    const box = el.querySelector(".chat-messages");
    const item = document.createElement("div");
    item.className = "chat-msg " + role;
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    bubble.textContent = content;
    item.appendChild(bubble);
    box.appendChild(item);
    scrollBottom(box);
    return bubble;
  }

  // 渲染聊天骨架；Enter 发送，Shift+Enter 换行
  function renderShell(el) {
    el.innerHTML = `
      <div class="chat-panel">
        <div class="chat-messages"></div>
        <div class="chat-input">
          <textarea class="form-control form-control-sm chat-text" rows="2"
                    maxlength="2000" placeholder="输入问题，Enter 发送，Shift+Enter 换行"></textarea>
          <button type="button" class="btn btn-sm btn-primary chat-send">发送</button>
        </div>
      </div>
    `;

    const input = el.querySelector(".chat-text");
    const button = el.querySelector(".chat-send");
    button.addEventListener("click", function () {
      send(el);
    });
    input.addEventListener("keydown", function (event) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        send(el);
      }
    });
  }

  // 历史按 lead_id + 当前登录用户隔离；没有历史时显示欢迎语
  async function loadHistory(el) {
    const box = el.querySelector(".chat-messages");
    const leadId = el.getAttribute("data-lead-id");
    if (!box || !leadId) return;
    box.innerHTML = "";
    try {
      const res = await App.fetchJson(
        "/chat/history?lead_id=" + encodeURIComponent(leadId)
      );
      if (res.code === 401) {
        location.href = "/login";
        return;
      }
      if (res.code !== 0) {
        appendMessage(el, "assistant", "加载历史失败：" + (res.msg || ""));
        return;
      }
      const records = res.data || [];
      if (!records.length) {
        appendMessage(el, "assistant", "你好，我可以根据本项目的商机、跟进、招投标、立项资料回答问题。");
        return;
      }
      records.forEach(function (record) {
        appendMessage(el, record.role === "user" ? "user" : "assistant", record.content);
      });
    } catch (err) {
      appendMessage(el, "assistant", "加载历史失败：" + err.message);
    }
  }

  // 流式发送：用原生 fetch 读取 ReadableStream，不能走 App.postJson（它会等完整响应）
  async function send(el) {
    // dataset.sending 防止同一个 pane 并发发送
    if (el.dataset.sending === "1") return;
    const leadId = el.getAttribute("data-lead-id");
    if (!leadId) return;

    const input = el.querySelector(".chat-text");
    const button = el.querySelector(".chat-send");
    const text = input.value.trim();
    if (!text) return;

    appendMessage(el, "user", text);
    input.value = "";
    const bubble = appendMessage(el, "assistant", "");
    el.dataset.sending = "1";
    button.disabled = true;
    button.textContent = "回答中...";

    try {
      const response = await fetch("/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lead_id: Number(leadId), message: text }),
      });
      if (response.status === 401) {
        location.href = "/login";
        return;
      }
      if (!response.ok) {
        let detail = "";
        try {
          detail = (await response.json()).detail || "";
        } catch (err) {
          /* 非 JSON 响应 */
        }
        throw new Error(detail || ("HTTP " + response.status));
      }

      // 逐块读取纯文本并更新助手气泡；textContent 同时避免 XSS
      const box = el.querySelector(".chat-messages");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let content = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        content += decoder.decode(value, { stream: true });
        bubble.textContent = content;
        scrollBottom(box);
      }
      if (!content) bubble.textContent = "（无回答）";
    } catch (err) {
      bubble.textContent = "回答失败：" + err.message;
    } finally {
      el.dataset.sending = "0";
      button.disabled = false;
      button.textContent = "发送";
      scrollBottom(el.querySelector(".chat-messages"));
    }
  }

  // map.js 每次打开 InfoWindow 都会调用；同一个 pane 对同一个 lead 只初始化一次
  function init(id) {
    const el = pane();
    if (!el) return;
    if (el.dataset.initialized === String(id)) return;
    el.dataset.initialized = String(id);
    el.dataset.sending = "0";
    renderShell(el);
    loadHistory(el);
  }

  window.ChatPage = { init };
})();
