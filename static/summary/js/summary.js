/* 项目总结：四项并行结果。
 * 并行计算在后端 RunnableParallel 完成，前端只负责触发、展示和缓存加载。
 */
(function () {
  "use strict";

  function pane() {
    return document.getElementById("iwSummary");
  }

  function formatTime(value) {
    return String(value || "").slice(0, 16);
  }

  function showAlert(el, message, type) {
    const alert = el.querySelector(".summary-alert");
    if (!alert) return;
    alert.className = "alert alert-" + type + " py-2 small mt-2";
    alert.textContent = message;
  }

  function hideAlert(el) {
    const alert = el.querySelector(".summary-alert");
    if (alert) alert.className = "alert py-2 small d-none mt-2";
  }

  function renderShell(el) {
    el.innerHTML = `
      <div class="summary-head d-flex align-items-center gap-2">
        <button type="button" class="btn btn-sm btn-primary summary-run">总结</button>
        <span class="text-muted small summary-hint">对本项目资料进行四项并行分析</span>
        <span class="summary-spinner spinner-border spinner-border-sm text-primary d-none"></span>
      </div>
      <div class="summary-alert alert py-2 small d-none mt-2"></div>
      <div class="summary-result mt-3"></div>
    `;
    el.querySelector(".summary-run").addEventListener("click", function () {
      generate(el);
    });
  }

  // 数据契约：tags 数组，summary/analysis/lessons 文本，update_time 时间
  function renderResult(el, data) {
    const box = el.querySelector(".summary-result");
    const button = el.querySelector(".summary-run");
    if (!data) {
      box.innerHTML = `<div class="summary-empty">暂无总结，点击「总结」生成。</div>`;
      button.textContent = "总结";
      return;
    }

    button.textContent = "重新总结";
    const tags = (data.tags || []).map(function (tag) {
      return `<span class="badge text-bg-light border">${App.esc(tag)}</span>`;
    }).join("");

    box.innerHTML = `
      <section class="summary-section">
        <h6>标签</h6>
        <div class="summary-tags">${tags || '<span class="text-muted small">暂无</span>'}</div>
      </section>
      <section class="summary-section">
        <h6>摘要</h6>
        <p class="summary-text">${App.esc(data.summary || "暂无")}</p>
      </section>
      <section class="summary-section">
        <h6>项目分析</h6>
        <p class="summary-text">${App.esc(data.analysis || "暂无")}</p>
      </section>
      <section class="summary-section">
        <h6>经验总结</h6>
        <p class="summary-text">${App.esc(data.lessons || "暂无")}</p>
      </section>
      <div class="summary-time">更新时间：${App.esc(formatTime(data.update_time))}</div>
    `;
  }

  async function load(el) {
    const leadId = el.getAttribute("data-lead-id");
    if (!leadId) return;
    try {
      const res = await App.fetchJson(
        "/summary/detail?lead_id=" + encodeURIComponent(leadId)
      );
      if (res.code === 401) {
        location.href = "/login";
        return;
      }
      if (res.code !== 0) {
        showAlert(el, res.msg || "加载失败。", "danger");
        return;
      }
      renderResult(el, res.data || null);
    } catch (err) {
      showAlert(el, "加载失败：" + err.message, "danger");
    }
  }

  // 生成期间禁用按钮；finally 根据是否已有结果恢复“总结/重新总结”
  async function generate(el) {
    const leadId = el.getAttribute("data-lead-id");
    if (!leadId) return;

    const button = el.querySelector(".summary-run");
    const spinner = el.querySelector(".summary-spinner");
    button.disabled = true;
    button.textContent = "总结中...";
    spinner.classList.remove("d-none");
    hideAlert(el);

    try {
      const res = await App.postJson("/summary/generate", {
        lead_id: Number(leadId),
      });
      if (res.code === 401) {
        location.href = "/login";
        return;
      }
      if (res.code !== 0) {
        showAlert(el, res.msg || "总结失败。", "danger");
        return;
      }
      renderResult(el, res.data || null);
    } catch (err) {
      showAlert(el, "总结失败：" + err.message, "danger");
    } finally {
      button.disabled = false;
      button.textContent = el.querySelector(".summary-result .summary-section")
        ? "重新总结"
        : "总结";
      spinner.classList.add("d-none");
    }
  }

  // 懒加载：进入总结页签时才加载已缓存的总结；每个 pane 只渲染一次骨架
  document.addEventListener("shown.bs.tab", function (event) {
    if (event.target.getAttribute("data-bs-target") !== "#iwSummary") return;
    const el = pane();
    if (!el || !el.getAttribute("data-lead-id")) return;
    if (el.dataset.initialized !== "1") {
      el.dataset.initialized = "1";
      renderShell(el);
    }
    load(el);
  });
})();
