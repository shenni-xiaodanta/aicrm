/* 附件管理：类型下拉 + 说明 + 多附件 + 记录列表。
 * 招投标 #iwBid 和立项 #iwInit 两个页签共用此模块，通过 group 区分文件类型。
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
  // 页签分组 -> 固定文件类型，同时用于下拉选项和列表过滤
  const GROUPS = {
    bidding: ["招标文件", "投标文件", "投标结果"],
    initiation: ["方案", "报价", "合同"],
  };

  // 两个 pane 各自维护待上传列表；WeakMap 随 DOM 节点回收，不会串数据
  const states = new WeakMap();

  function stateOf(pane) {
    if (!states.has(pane)) {
      states.set(pane, { pending: [] });
    }
    return states.get(pane);
  }

  function formatSize(size) {
    if (size >= 1024 * 1024) return (size / 1024 / 1024).toFixed(1) + " MB";
    if (size >= 1024) return (size / 1024).toFixed(0) + " KB";
    return size + " B";
  }

  function formatTime(value) {
    return String(value || "").slice(0, 16);
  }

  function showAlert(pane, message, type) {
    const alert = pane.querySelector(".attachment-alert");
    if (!alert) return;
    alert.className = "alert alert-" + type + " py-2 small mt-2";
    alert.textContent = message;
  }

  function hideAlert(pane) {
    const alert = pane.querySelector(".attachment-alert");
    if (alert) alert.className = "alert py-2 small d-none mt-2";
  }

  function renderShell(pane, group) {
    const categories = GROUPS[group] || [];
    pane.innerHTML = `
      <div class="attachment-head">
        <select class="form-select form-select-sm attachment-category">
          ${categories.map(function (category) {
            return `<option value="${App.esc(category)}">${App.esc(category)}</option>`;
          }).join("")}
        </select>
        <textarea class="form-control form-control-sm mt-2 attachment-desc" rows="3"
                  maxlength="2000" placeholder="输入说明文字..."></textarea>
        <div class="d-flex align-items-center gap-2 mt-2 flex-wrap">
          <label class="btn btn-sm btn-outline-secondary mb-0">
            选择附件
            <input class="attachment-file-input" type="file" multiple hidden
                   accept="${ALLOWED.join(",")}">
          </label>
          <span class="attachment-count text-muted small"></span>
          <button type="button" class="btn btn-sm btn-primary ms-auto attachment-submit">提交</button>
        </div>
        <div class="attachment-pending"></div>
        <div class="attachment-alert alert py-2 small d-none mt-2"></div>
      </div>
      <div class="attachment-list mt-3"></div>
    `;

    pane.querySelector(".attachment-file-input").addEventListener("change", function () {
      addFiles(pane, this);
    });
    pane.querySelector(".attachment-submit").addEventListener("click", function () {
      submit(pane, group);
    });
    renderPending(pane);
  }

  function addFiles(pane, input) {
    const state = stateOf(pane);
    for (const file of Array.from(input.files)) {
      const suffix = ("." + file.name.split(".").pop()).toLowerCase();
      if (!ALLOWED.includes(suffix)) {
        showAlert(pane, "不支持的附件类型：" + file.name, "danger");
        continue;
      }
      if (file.size > MAX_SIZE) {
        showAlert(pane, "附件超过 10MB：" + file.name, "danger");
        continue;
      }
      if (state.pending.length >= MAX_FILES) {
        showAlert(pane, "一次最多上传 " + MAX_FILES + " 个附件。", "danger");
        break;
      }
      if (!state.pending.some(function (item) {
        return item.name === file.name && item.size === file.size;
      })) {
        state.pending.push(file);
      }
    }
    input.value = "";
    renderPending(pane);
  }

  function renderPending(pane) {
    const state = stateOf(pane);
    const box = pane.querySelector(".attachment-pending");
    box.innerHTML = state.pending.map(function (file, index) {
      return `<div class="attachment-pending-item">
        <span class="attachment-pending-name">📎 ${App.esc(file.name)}</span>
        <span class="text-muted small">${formatSize(file.size)}</span>
        <button type="button" class="btn btn-sm btn-link text-danger p-0"
                data-index="${index}">移除</button>
      </div>`;
    }).join("");

    const count = pane.querySelector(".attachment-count");
    count.textContent = state.pending.length ? "已选 " + state.pending.length + " 个" : "";

    box.querySelectorAll("[data-index]").forEach(function (button) {
      button.addEventListener("click", function () {
        state.pending.splice(Number(button.dataset.index), 1);
        renderPending(pane);
      });
    });
  }

  function renderList(box, records) {
    if (!records.length) {
      box.innerHTML = `<div class="lead-empty">暂无附件记录</div>`;
      return;
    }
    box.innerHTML = records.map(function (record) {
      const files = (record.files || []).map(function (file) {
        return `<a class="attachment-file" href="/attachment/file/${file.id}"
                   target="_blank" rel="noopener noreferrer">📎 ${App.esc(file.original_name)}</a>`;
      }).join("");
      return `<div class="attachment-item">
        <div class="d-flex justify-content-between align-items-center">
          <span class="badge text-bg-light border">${App.esc(record.category)}</span>
          <span class="text-muted small">${App.esc(formatTime(record.create_time))}</span>
        </div>
        ${record.description ? `<div class="attachment-desc">${App.esc(record.description)}</div>` : ""}
        ${files ? `<div class="attachment-files">${files}</div>` : ""}
      </div>`;
    }).join("");
  }

  // 一次拉取该商机全部附件，再按当前页签的分组在前端过滤
  async function loadList(pane, group) {
    const box = pane.querySelector(".attachment-list");
    const leadId = pane.getAttribute("data-lead-id");
    if (!box || !leadId) return;
    try {
      const res = await App.fetchJson(
        "/attachment/list?lead_id=" + encodeURIComponent(leadId)
      );
      if (res.code === 401) {
        location.href = "/login";
        return;
      }
      if (res.code !== 0) {
        box.innerHTML = `<div class="lead-empty">加载失败：${App.esc(res.msg || "")}</div>`;
        return;
      }
      const categories = new Set(GROUPS[group] || []);
      const records = (res.data || []).filter(function (record) {
        return categories.has(record.category);
      });
      renderList(box, records);
    } catch (err) {
      box.innerHTML = `<div class="lead-empty">加载失败：${App.esc(err.message)}</div>`;
    }
  }

  // multipart 上传：类型 + 说明至少填一项，附件在本地暂存后一次性提交
  async function submit(pane, group) {
    const state = stateOf(pane);
    const category = pane.querySelector(".attachment-category").value;
    const description = pane.querySelector(".attachment-desc").value.trim();
    if (!category) {
      showAlert(pane, "请选择附件类型。", "danger");
      return;
    }
    if (!description && !state.pending.length) {
      showAlert(pane, "请填写说明或选择附件。", "danger");
      return;
    }

    const button = pane.querySelector(".attachment-submit");
    button.disabled = true;
    button.textContent = "提交中...";

    const form = new FormData();
    form.append("lead_id", pane.getAttribute("data-lead-id"));
    form.append("category", category);
    form.append("description", description);
    state.pending.forEach(function (file) {
      form.append("files", file);
    });

    try {
      const response = await fetch("/attachment/add", { method: "POST", body: form });
      if (!response.ok) throw new Error("HTTP " + response.status);
      const res = await response.json();
      if (res.code === 401) {
        location.href = "/login";
        return;
      }
      if (res.code !== 0) {
        showAlert(pane, res.msg || "提交失败。", "danger");
        return;
      }
      pane.querySelector(".attachment-desc").value = "";
      state.pending = [];
      renderPending(pane);
      hideAlert(pane);
      await loadList(pane, group);
    } catch (err) {
      showAlert(pane, "提交失败：" + err.message, "danger");
    } finally {
      button.disabled = false;
      button.textContent = "提交";
    }
  }

  // 两个页签分别映射到 bidding / initiation；每个 pane 只渲染一次骨架
  document.addEventListener("shown.bs.tab", function (event) {
    const target = event.target.getAttribute("data-bs-target");
    let pane = null;
    let group = null;
    if (target === "#iwBid") {
      pane = document.getElementById("iwBid");
      group = "bidding";
    } else if (target === "#iwInit") {
      pane = document.getElementById("iwInit");
      group = "initiation";
    }
    if (!pane || !pane.getAttribute("data-lead-id")) return;

    if (pane.dataset.initialized !== "1") {
      pane.dataset.initialized = "1";
      renderShell(pane, group);
    }
    loadList(pane, group);
  });
})();
