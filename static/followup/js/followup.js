/* 跟进记录：文本框 + 附件 + 时间轴。
 * 懒加载 #iwFollow 页签；pendingFiles 在点击提交前只存在于浏览器。
 */
(function () {
  "use strict";

  const MAX_SIZE = 10 * 1024 * 1024;
  const MAX_FILES = 10;
  const ALLOWED = [
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf", ".txt", ".csv",
    ".zip", ".rar", ".7z",
  ];

  // 只有一个 #iwFollow 页签，使用模块级状态即可；
  // initializedPane 记录已经渲染过的 DOM 节点，用于区分“切换页签”和“打开新商机”
  let pendingFiles = [];
  let currentLeadId = null;
  let initializedPane = null;

  function pane() {
    return document.getElementById("iwFollow");
  }

  function formatSize(size) {
    if (size >= 1024 * 1024) return (size / 1024 / 1024).toFixed(1) + " MB";
    if (size >= 1024) return (size / 1024).toFixed(0) + " KB";
    return size + " B";
  }

  function formatTime(value) {
    return String(value || "").slice(0, 16);
  }

  function showAlert(message, type) {
    const el = pane();
    const alert = el && el.querySelector("#followAlert");
    if (!alert) return;
    alert.className = "alert alert-" + type + " py-2 small mt-2";
    alert.textContent = message;
  }

  function hideAlert() {
    const el = pane();
    const alert = el && el.querySelector("#followAlert");
    if (alert) alert.className = "alert py-2 small d-none mt-2";
  }

  // 渲染输入区、附件选择和空时间轴；附件只在本地暂存，提交时才上传
  function renderShell(el) {
    el.innerHTML = `
      <div class="follow-head">
        <textarea id="followContent" class="form-control form-control-sm" rows="3"
                  maxlength="2000" placeholder="输入本次跟进内容..."></textarea>
        <div class="d-flex align-items-center gap-2 mt-2 flex-wrap">
          <label class="btn btn-sm btn-outline-secondary mb-0">
            选择附件
            <input id="followFileInput" type="file" multiple hidden
                   accept="${ALLOWED.join(",")}">
          </label>
          <span id="followFileCount" class="text-muted small"></span>
          <button id="followSubmit" type="button" class="btn btn-sm btn-primary ms-auto">添加跟进</button>
        </div>
        <div id="followPending" class="follow-pending"></div>
        <div id="followAlert" class="alert py-2 small d-none mt-2"></div>
      </div>
      <div id="followTimeline" class="follow-timeline mt-3"></div>
    `;

    el.querySelector("#followFileInput").addEventListener("change", function () {
      addFiles(this);
    });
    el.querySelector("#followSubmit").addEventListener("click", submit);
    renderPending(el);
  }

  // 类型/大小/数量校验；input.value="" 允许再次选择同一个文件
  function addFiles(input) {
    const el = pane();
    for (const file of Array.from(input.files)) {
      const suffix = ("." + file.name.split(".").pop()).toLowerCase();
      if (!ALLOWED.includes(suffix)) {
        showAlert("不支持的附件类型：" + file.name, "danger");
        continue;
      }
      if (file.size > MAX_SIZE) {
        showAlert("附件超过 10MB：" + file.name, "danger");
        continue;
      }
      if (pendingFiles.length >= MAX_FILES) {
        showAlert("一次最多上传 " + MAX_FILES + " 个附件。", "danger");
        break;
      }
      if (!pendingFiles.some(function (item) {
        return item.name === file.name && item.size === file.size;
      })) {
        pendingFiles.push(file);
      }
    }
    input.value = "";
    renderPending(el);
  }

  // 待上传列表：按索引移除后整体重渲染；文件名用 App.esc 转义
  function renderPending(el) {
    const box = el.querySelector("#followPending");
    box.innerHTML = pendingFiles.map(function (file, index) {
      return `<div class="follow-pending-item">
        <span class="follow-pending-name">📎 ${App.esc(file.name)}</span>
        <span class="text-muted small">${formatSize(file.size)}</span>
        <button type="button" class="btn btn-sm btn-link text-danger p-0"
                data-index="${index}">移除</button>
      </div>`;
    }).join("");

    const count = el.querySelector("#followFileCount");
    count.textContent = pendingFiles.length ? "已选 " + pendingFiles.length + " 个" : "";

    box.querySelectorAll("[data-index]").forEach(function (button) {
      button.addEventListener("click", function () {
        pendingFiles.splice(Number(button.dataset.index), 1);
        renderPending(el);
      });
    });
  }

  function renderTimeline(box, records) {
    if (!records.length) {
      box.innerHTML = `<div class="lead-empty">暂无跟进记录</div>`;
      return;
    }
    box.innerHTML = records.map(function (record) {
      const files = (record.files || []).map(function (file) {
        return `<a class="follow-file" href="/followup/file/${file.id}"
                   target="_blank" rel="noopener noreferrer">📎 ${App.esc(file.original_name)}</a>`;
      }).join("");
      return `<div class="follow-item">
        <div class="follow-time">${App.esc(formatTime(record.create_time))}</div>
        <div class="follow-content">${App.esc(record.content)}</div>
        ${files ? `<div class="follow-files">${files}</div>` : ""}
      </div>`;
    }).join("");
  }

  async function loadList() {
    const el = pane();
    if (!el || !currentLeadId) return;
    const box = el.querySelector("#followTimeline");
    if (!box) return;
    try {
      const res = await App.fetchJson(
        "/followup/list?lead_id=" + encodeURIComponent(currentLeadId)
      );
      if (res.code === 401) {
        location.href = "/login";
        return;
      }
      if (res.code !== 0) {
        box.innerHTML = `<div class="lead-empty">加载失败：${App.esc(res.msg || "")}</div>`;
        return;
      }
      renderTimeline(box, res.data || []);
    } catch (err) {
      box.innerHTML = `<div class="lead-empty">加载失败：${App.esc(err.message)}</div>`;
    }
  }

  // multipart 上传必须用原生 fetch + FormData，不能走 App.postJson（它发 JSON）
  async function submit() {
    const el = pane();
    if (!el || !currentLeadId) return;
    const content = el.querySelector("#followContent").value.trim();
    if (!content) {
      showAlert("请输入跟进内容。", "danger");
      return;
    }

    const button = el.querySelector("#followSubmit");
    button.disabled = true;
    button.textContent = "提交中...";

    const form = new FormData();
    form.append("lead_id", currentLeadId);
    form.append("content", content);
    pendingFiles.forEach(function (file) {
      form.append("files", file);
    });

    try {
      const response = await fetch("/followup/add", { method: "POST", body: form });
      if (!response.ok) throw new Error("HTTP " + response.status);
      const res = await response.json();
      if (res.code === 401) {
        location.href = "/login";
        return;
      }
      if (res.code !== 0) {
        showAlert(res.msg || "提交失败。", "danger");
        return;
      }
      el.querySelector("#followContent").value = "";
      pendingFiles = [];
      renderPending(el);
      hideAlert();
      await loadList();
    } catch (err) {
      showAlert("提交失败：" + err.message, "danger");
    } finally {
      button.disabled = false;
      button.textContent = "添加跟进";
    }
  }

  // 委托监听页签切换；只在进入跟进页签时加载，避免打开弹窗就发请求。
  // initializedPane !== el 说明是新的 InfoWindow 内容，需要重建输入区。
  document.addEventListener("shown.bs.tab", function (event) {
    if (event.target.getAttribute("data-bs-target") !== "#iwFollow") return;
    const el = pane();
    if (!el) return;
    const leadId = el.getAttribute("data-lead-id");
    if (!leadId) return;

    if (initializedPane !== el) {
      initializedPane = el;
      currentLeadId = leadId;
      pendingFiles = [];
      renderShell(el);
    } else {
      currentLeadId = leadId;
    }
    loadList();
  });
})();
