/* 负责人：下拉变更 + 变更时间轴。
 * 懒加载 #iwOwner 页签；变更成功后直接用响应重新渲染，避免再次请求。
 */
(function () {
  "use strict";

  function pane() {
    return document.getElementById("iwOwner");
  }

  function formatTime(value) {
    return String(value || "").slice(0, 16);
  }

  function showAlert(el, message, type) {
    const alert = el.querySelector(".owner-alert");
    if (!alert) return;
    alert.className = "alert alert-" + type + " py-2 small mt-2";
    alert.textContent = message;
  }

  function hideAlert(el) {
    const alert = el.querySelector(".owner-alert");
    if (alert) alert.className = "alert py-2 small d-none mt-2";
  }

  function renderShell(el) {
    el.innerHTML = `
      <div class="owner-head">
        <div class="small text-muted mb-1">当前负责人：<span class="owner-current">未指定</span></div>
        <select class="form-select form-select-sm owner-select"></select>
        <textarea class="form-control form-control-sm mt-2 owner-note-input" rows="2"
                  maxlength="500" placeholder="变更说明（选填）"></textarea>
        <div class="text-end mt-2">
          <button type="button" class="btn btn-sm btn-primary owner-submit">变更负责人</button>
        </div>
        <div class="owner-alert alert py-2 small d-none mt-2"></div>
      </div>
      <div class="owner-timeline mt-3"></div>
    `;
    el.querySelector(".owner-submit").addEventListener("click", function () {
      change(el);
    });
  }

  // 用 Number 比较，兼容接口把 id 返回成字符串的情况
  function renderDetail(el, detail) {
    el.querySelector(".owner-current").textContent = detail.owner_name || "未指定";

    const select = el.querySelector(".owner-select");
    select.innerHTML = (detail.users || []).map(function (user) {
      const selected = Number(user.id) === Number(detail.owner_id) ? "selected" : "";
      return `<option value="${user.id}" ${selected}>${App.esc(user.name)}</option>`;
    }).join("");

    renderChanges(el, detail.changes || []);
  }

  function renderChanges(el, changes) {
    const box = el.querySelector(".owner-timeline");
    if (!changes.length) {
      box.innerHTML = `<div class="lead-empty">暂无负责人变更记录</div>`;
      return;
    }
    box.innerHTML = changes.map(function (item) {
      return `<div class="owner-item">
        <div class="owner-time">${App.esc(formatTime(item.create_time))}</div>
        <div class="owner-change">${App.esc(item.old_name)} → ${App.esc(item.new_name)}</div>
        ${item.note ? `<div class="owner-note">${App.esc(item.note)}</div>` : ""}
      </div>`;
    }).join("");
  }

  async function load(el) {
    const leadId = el.getAttribute("data-lead-id");
    if (!leadId) return;
    try {
      const res = await App.fetchJson(
        "/owner/detail?lead_id=" + encodeURIComponent(leadId)
      );
      if (res.code === 401) {
        location.href = "/login";
        return;
      }
      if (res.code !== 0) {
        showAlert(el, res.msg || "加载失败。", "danger");
        return;
      }
      renderDetail(el, res.data || {});
    } catch (err) {
      showAlert(el, "加载失败：" + err.message, "danger");
    }
  }

  // 提交变更：lead_id / owner_id 统一转 Number，成功后清空说明并重新渲染
  async function change(el) {
    const leadId = el.getAttribute("data-lead-id");
    const ownerId = Number(el.querySelector(".owner-select").value);
    const note = el.querySelector(".owner-note-input").value.trim();
    if (!leadId || !ownerId) {
      showAlert(el, "请选择负责人。", "danger");
      return;
    }

    const button = el.querySelector(".owner-submit");
    button.disabled = true;
    button.textContent = "提交中...";
    try {
      const res = await App.postJson("/owner/change", {
        lead_id: Number(leadId),
        owner_id: ownerId,
        note: note,
      });
      if (res.code === 401) {
        location.href = "/login";
        return;
      }
      if (res.code !== 0) {
        showAlert(el, res.msg || "变更失败。", "danger");
        return;
      }
      el.querySelector(".owner-note-input").value = "";
      hideAlert(el);
      renderDetail(el, res.data || {});
    } catch (err) {
      showAlert(el, "变更失败：" + err.message, "danger");
    } finally {
      button.disabled = false;
      button.textContent = "变更负责人";
    }
  }

  // 懒加载：进入负责人页签时才请求详情；每个 pane 只渲染一次骨架
  document.addEventListener("shown.bs.tab", function (event) {
    if (event.target.getAttribute("data-bs-target") !== "#iwOwner") return;
    const el = pane();
    if (!el || !el.getAttribute("data-lead-id")) return;
    if (el.dataset.initialized !== "1") {
      el.dataset.initialized = "1";
      renderShell(el);
    }
    load(el);
  });
})();
