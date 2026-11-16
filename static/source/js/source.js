/* 采集任务页 + 站点管理页（对齐 demo 定稿的用户视角）。
 *
 * 分工（P1 起，本批收敛）：
 *   - 地区不再由前端硬编码省市树，采集点来自 crm_crawl_region（GET /crawl/regions）
 *   - 解析配方归站点模板（crm_crawl_site），人不再手填 base_domain / list_url
 *   - 一次采集 = 后台任务，本页只负责发起 + 轮询进度 + 展示历史
 *   - 「站点管理」仅 admin：粘一个列表页 URL → 识别 → 真页面回验 → 入库；
 *     站点编码按域名自动生成、站点名称由模型从页面推断，无需手填
 *   - 地区登记是独立动作（POST /crawl/regions）：一个站点模板可挂 N 个地区，
 *     用户只回答「用在哪个地区」，入口地址从配方反推
 *   - 没有「停用」这一层：站点失效就删除（软删，历史任务与商机保留）
 */
(function () {
  "use strict";

  // ------------------------------------------------------------------
  // 展示口径：状态与停止原因都要说人话
  // ------------------------------------------------------------------
  const STATUS = {
    running: ["采集中", "text-bg-primary"],
    success: ["完成", "text-bg-success"],
    partial: ["部分完成", "text-bg-warning"],
    failed: ["失败", "text-bg-danger"],
    canceled: ["已取消", "text-bg-secondary"],
  };

  // 用户看「max_pages」不知道是什么，翻译成一句人话
  const STOP_TEXT = {
    no_new: "连续 5 条都是已有公告，增量已到底，自动停止",
    max_pages: "已到该站点的翻页上限",
    empty_page: "翻到空页，已停止",
    error: "采集中断，原因见下方明细",
    manual: "手动取消",
  };

  const POLL_INTERVAL = 2500;
  // 轮询连续失败要止损：任务被删 / 接口挂了不能无限重试下去
  const POLL_MAX_FAILS = 10;

  let role = "";

  // ------------------------------------------------------------------
  // 小工具
  // ------------------------------------------------------------------
  function $(id) {
    return document.getElementById(id);
  }

  async function jsonOrThrow(url) {
    const res = await App.fetchJson(url);
    if (res.code === 401) {
      location.href = "/login";
      throw new Error("登录已失效");
    }
    if (res.code === 403) throw new Error("没有权限执行该操作");
    if (res.code !== 0) throw new Error(res.msg || "请求失败");
    return res.data;
  }

  /* 「今天 18:32 / 昨天 09:10 / 11-13 16:44」——比 ISO 串好读，也不占宽度 */
  function humanTime(value) {
    if (!value) return "";
    const date = new Date(String(value).replace(" ", "T"));
    if (isNaN(date.getTime())) return String(value).slice(0, 16);
    const pad = function (n) { return String(n).padStart(2, "0"); };
    const hm = pad(date.getHours()) + ":" + pad(date.getMinutes());
    const now = new Date();
    if (date.toDateString() === now.toDateString()) return "今天 " + hm;
    const yesterday = new Date(now.getTime() - 86400000);
    if (date.toDateString() === yesterday.toDateString()) return "昨天 " + hm;
    return (date.getMonth() + 1) + "-" + pad(date.getDate()) + " " + hm;
  }

  /* 地区展示名：省 · 市；直辖市省市同名时不重复写一遍 */
  function areaLabel(item) {
    const province = (item.province || "").trim();
    const city = (item.city || "").trim();
    if (province && city && province !== city) return province + " · " + city;
    return city || province || "未命名地区";
  }

  function showAlert(el, message, type) {
    el.className = "small ms-auto alert alert-" + (type || "danger") + " py-1 px-2";
    el.textContent = message;
  }

  function hideAlert(el) {
    el.className = "small ms-auto d-none";
    el.textContent = "";
  }

  let validModal = null;

  /* 必填校验弹窗：空值提交弹它 + 输入框红框，而不是在页面上写死一句提示 */
  function showValid(message) {
    $("validMsg").textContent = message;
    if (!validModal) validModal = new bootstrap.Modal($("validModal"));
    validModal.show();
  }

  let confirmAction = null;
  let confirmModal = null;

  /* 删除类操作统一走二次确认：这类动作不可逆，绝不能一点就删 */
  function askConfirm(message, hint, action) {
    $("confirmMsg").textContent = message;
    $("confirmHint").textContent = hint || "";
    confirmAction = action;
    if (!confirmModal) confirmModal = new bootstrap.Modal($("confirmModal"));
    confirmModal.show();
  }

  $("confirmYes").addEventListener("click", function () {
    const action = confirmAction;
    confirmAction = null;
    if (action) action();
  });

  /* 输入即清除错误态：错误提示跟着用户的操作消失，不要一直红着 */
  function clearErrorOnInput(input) {
    input.addEventListener("input", function () {
      input.classList.remove("is-invalid");
      const field = input.closest(".field");
      if (field) field.classList.remove("has-error");
    });
  }

  // ------------------------------------------------------------------
  // 顶层页签
  // ------------------------------------------------------------------
  const tabs = document.querySelectorAll("#pageTabs .page-tab");
  const pages = {
    work: $("page-work"),
    task: $("page-task"),
    site: $("page-site"),
  };

  function switchPage(name) {
    tabs.forEach(function (tab) {
      tab.classList.toggle("active", tab.dataset.page === name);
    });
    Object.keys(pages).forEach(function (key) {
      pages[key].classList.toggle("d-none", key !== name);
    });
    // 顶栏那组数字只跟工作台有关，别的页面留着只会干扰
    $("workbar").classList.toggle("d-none", name !== "work");
    // 工作台从 display:none 回来后，若当前是地图视图，画布尺寸已失效
    if (name === "work" && window.MapPage && window.MapPage.onShow) {
      window.MapPage.onShow();
    }
  }

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      switchPage(tab.dataset.page);
      // 每次进入都重新拉：管理员可能刚删过地区 / 采集刚结束
      if (tab.dataset.page === "task") loadTaskPage();
      if (tab.dataset.page === "site") loadSiteList();
    });
  });

  // ------------------------------------------------------------------
  // 采集任务页：选地区 → 发起 → 轮询进度 → 历史
  // ------------------------------------------------------------------
  const taskAlert = $("taskAlert");
  const regionSelect = $("crawlRegionSelect");
  const regionInfo = $("crawlRegionInfo");
  const startBtn = $("crawlStart");
  const progressEl = $("crawlProgress");
  const statusEl = $("crawlStatus");
  const taskNoEl = $("crawlTaskNo");
  const spinEl = $("crawlSpin");
  const runningTextEl = $("crawlRunningText");
  const barEl = $("crawlBar");
  const totalEl = $("crawlTotal");
  const newEl = $("crawlNew");
  const dupEl = $("crawlDup");
  const failEl = $("crawlFail");
  const failStatEl = $("crawlFailStat");
  const stopTextEl = $("crawlStopText");
  const failDetailEl = $("crawlFailDetail");
  const gotoBtn = $("crawlGoto");
  const historyEl = $("taskHistory");

  let regions = [];
  let pollTimer = null;
  let polling = false;
  // 采集结束后「查看商机」要知道跳到哪个地区，这里记住最近一次的结果
  let lastArea = null;   // { province, city }
  // 进度条没有真实总页数可比，用不确定推进：每轮 +8% 封顶 90%，
  // 结束时拉满——比一个永远 0% 的条更有「在动」的信心
  let barPct = 2;

  function currentRegion() {
    return regions.find(function (r) {
      return String(r.id) === regionSelect.value;
    }) || null;
  }

  function siteNameOf(task) {
    const region = regions.find(function (r) {
      return String(r.id) === String(task.region_id);
    });
    return (region && region.site_name) || task.site_name || task.site_code || "站点";
  }

  /* 「全国」表示这个站点本身就是全国性的（如中国政府采购网）：公告来自全国各地，
   * 此时不能把工作台收敛到某个省，否则一条都筛不出来 */
  function isNationwideArea(area) {
    const wide = function (text) {
      const value = String(text || "").trim();
      return !value || value === "全国" || value === "全国性";
    };
    return wide(area && area.province) && wide(area && area.city);
  }

  /* 跳到商机工作台并聚焦到该地区：采集结束后的一步入口，
   * 也是采集记录每行的「查看商机」——用户不用自己再去两个下拉里挑一遍 */
  function goToRegion(area) {
    switchPage("work");
    if (window.MapPage && window.MapPage.focusRegion) {
      window.MapPage.focusRegion(area && area.province, area && area.city);
    }
  }

  function renderRegions() {
    const keep = regionSelect.value;
    regionSelect.innerHTML = "";

    if (!regions.length) {
      regionSelect.appendChild(new Option("（还没有可采集的地区）", ""));
      regionSelect.disabled = true;
      startBtn.disabled = true;
      // 普通用户进不去站点管理，就别指一扇他打不开的门
      regionInfo.textContent = role === "admin"
        ? "还没有采集地区：在「站点管理」粘贴一个公告列表页网址就能接入。"
        : "还没有可采集的地区，请联系管理员开通。";
      return;
    }

    const usable = regions.filter(function (r) { return r.can_crawl; });
    const blocked = regions.filter(function (r) { return !r.can_crawl; });

    usable.forEach(function (region) {
      regionSelect.appendChild(new Option(areaLabel(region), region.id));
    });

    // 二期才支持浏览器渲染：本期列出来但不可选，避免用户以为地区丢了
    if (blocked.length) {
      const group = document.createElement("optgroup");
      group.label = "暂不支持（网站需要浏览器渲染）";
      blocked.forEach(function (region) {
        const option = new Option(areaLabel(region), region.id);
        option.disabled = true;
        group.appendChild(option);
      });
      regionSelect.appendChild(group);
    }

    regionSelect.disabled = usable.length === 0;
    if (keep && usable.some(function (r) { return String(r.id) === keep; })) {
      regionSelect.value = keep;
    } else if (usable.length) {
      regionSelect.value = usable[0].id;
    }
    renderRegionInfo();
    if (!usable.length) {
      // 只剩浏览器渲染的站点：说清为什么没得选，别让下拉停在一个空选项上
      regionInfo.textContent = "已接入的网站需要浏览器渲染，本期不支持采集。";
    }
  }

  function renderRegionInfo() {
    const region = currentRegion();
    if (!region) {
      regionInfo.textContent = "";
      startBtn.disabled = true;
      return;
    }
    if (!region.can_crawl) {
      regionInfo.textContent = "该网站需要浏览器渲染，本期不支持采集。";
      startBtn.disabled = true;
      return;
    }
    // 只说选中地区自己的事，不掺与它无关的全局状态
    regionInfo.textContent = region.last_crawl_at
      ? "最近采集：" + humanTime(region.last_crawl_at)
      : "还没有采集过，点右侧按钮开始";
    startBtn.disabled = false;
  }

  async function loadRegions() {
    try {
      regions = await jsonOrThrow("/crawl/regions");
      renderRegions();
    } catch (err) {
      if (err.message === "登录已失效") return;
      showAlert(taskAlert, "读取采集地区失败：" + err.message);
    }
  }

  function renderTask(task) {
    const meta = STATUS[task.status] || [task.status || "未知", "text-bg-secondary"];
    statusEl.textContent = meta[0];
    statusEl.className = "badge " + meta[1];
    taskNoEl.textContent = "#" + task.id + " · " + humanTime(task.started_at) + " 开始";

    totalEl.textContent = task.total_items || 0;
    newEl.textContent = task.new_count || 0;
    dupEl.textContent = task.dup_count || 0;
    failEl.textContent = task.fail_count || 0;
    // 没有失败就不摆一个 0 出来吓人
    failStatEl.classList.toggle("d-none", !(task.fail_count > 0));

    const running = task.status === "running";
    if (running) {
      barPct = Math.min(90, barPct + 8);
      spinEl.classList.remove("d-none");
      runningTextEl.innerHTML = "正在从「" + App.esc(siteNameOf(task)) +
        "」抓取最新公告，<b>可以离开页面</b>，任务会在后台继续。";
      gotoBtn.classList.add("d-none");
    } else {
      barPct = 100;
      spinEl.classList.add("d-none");
      runningTextEl.innerHTML = "本次采集" + meta[0] + "，" +
        (task.pages_crawled || 0) + " 页共扫到 " + (task.total_items || 0) + " 条公告。";
      // 结束态才给「查看商机」入口：采集中途跳走会让人以为任务被打断
      lastArea = { province: task.province, city: task.city };
      gotoBtn.textContent = isNationwideArea(lastArea)
        ? "查看全部商机 →"
        : "查看" + areaLabel(task) + "的商机 →";
      gotoBtn.classList.remove("d-none");
    }
    barEl.style.width = barPct + "%";

    if (task.stop_reason) {
      stopTextEl.textContent = STOP_TEXT[task.stop_reason] || task.stop_reason;
      stopTextEl.classList.remove("d-none");
    } else {
      stopTextEl.classList.add("d-none");
    }

    // 失败明细只取前 5 条：页面上不需要看全量，全量在任务表里
    const detail = Array.isArray(task.fail_detail) ? task.fail_detail : [];
    if (detail.length) {
      failDetailEl.innerHTML = detail.slice(0, 5).map(function (row) {
        return '<div class="text-danger">· ' + App.esc(row.title || row.url || "未知公告") +
          "：" + App.esc(row.reason || "") + "</div>";
      }).join("");
      failDetailEl.classList.remove("d-none");
    } else {
      failDetailEl.classList.add("d-none");
    }
  }

  function resetTaskPanel() {
    progressEl.classList.add("d-none");
    barPct = 2;
    barEl.style.width = barPct + "%";
  }

  function lockStart(text) {
    startBtn.disabled = true;
    startBtn.textContent = text;
  }

  function unlockStart() {
    startBtn.textContent = "开始采集";
    startBtn.disabled = false;
    renderRegionInfo();  // 选中地区不可采时仍要禁用
  }

  function stopPolling() {
    polling = false;
    if (pollTimer) {
      clearTimeout(pollTimer);
      pollTimer = null;
    }
  }

  async function finishTask(task) {
    stopPolling();
    unlockStart();
    renderTask(task);
    loadRegions();
    loadHistory(false);
    // 先等工作台把新数据拉回来，再收敛地区：顺序反了就是在旧数据上筛
    if (window.MapPage && window.MapPage.refresh) {
      try {
        await window.MapPage.refresh();
      } catch (err) {
        /* 工作台刷新失败不影响采集结果展示 */
      }
    }
    const scoped = lastArea && !isNationwideArea(lastArea);
    if (scoped && window.MapPage && window.MapPage.focusRegion) {
      window.MapPage.focusRegion(lastArea.province, lastArea.city);
    }
    const areaTip = scoped ? "「商机工作台」已定位到" + areaLabel(lastArea) + "。" : "";
    if (task.status === "success") {
      showAlert(taskAlert, "采集完成：新增 " + (task.new_count || 0) + " 条商机。" + areaTip, "success");
    } else if (task.status === "partial") {
      showAlert(taskAlert, "采集部分完成：新增 " + (task.new_count || 0) + " 条，失败 " +
        (task.fail_count || 0) + " 条。" + areaTip, "warning");
    } else {
      showAlert(taskAlert, "采集失败：" + (STOP_TEXT[task.stop_reason] || "原因见下方明细"), "danger");
    }
  }

  async function pollTask(taskId, fails) {
    if (!polling) return;
    fails = fails || 0;
    try {
      const task = await jsonOrThrow("/crawl/task/" + taskId);
      renderTask(task);
      if (task.status === "running") {
        pollTimer = setTimeout(function () { pollTask(taskId, 0); }, POLL_INTERVAL);
        return;
      }
      finishTask(task);
    } catch (err) {
      if (err.message === "登录已失效") return;
      // 单次失败不判死（网络抖一下就放弃会让用户以为采集挂了）
      if (fails + 1 >= POLL_MAX_FAILS) {
        stopPolling();
        unlockStart();
        showAlert(taskAlert, "查询采集进度失败：" + err.message + "（任务仍可能在后台运行）", "warning");
        return;
      }
      pollTimer = setTimeout(function () { pollTask(taskId, fails + 1); }, 5000);
    }
  }

  async function startCrawl() {
    const region = currentRegion();
    if (!region) {
      showAlert(taskAlert, "请先选择采集地区。", "warning");
      return;
    }
    hideAlert(taskAlert);
    resetTaskPanel();
    progressEl.classList.remove("d-none");
    statusEl.textContent = "启动中";
    statusEl.className = "badge text-bg-secondary";
    taskNoEl.textContent = "";
    lockStart("采集中...");

    try {
      const res = await App.postForm("/crawl/start", { region_id: region.id });
      if (res.code === 401) {
        location.href = "/login";
        return;
      }
      if (res.code !== 0) throw new Error(res.msg || "发起采集失败");
      polling = true;
      barPct = 2;
      // 先拉一次快照，再进入间隔轮询——第一页抓完前就有「已抓取 x 条」
      pollTask(res.data.task_id);
    } catch (err) {
      unlockStart();
      resetTaskPanel();
      showAlert(taskAlert, "发起采集失败：" + err.message);
    }
  }

  // ------------------------------------------------------------------
  // 采集记录
  // ------------------------------------------------------------------
  function historyRow(task) {
    const meta = STATUS[task.status] || [task.status || "未知", "text-bg-secondary"];
    let summary;
    if (task.status === "running") {
      summary = "已抓取 " + (task.total_items || 0) + " 条公告";
    } else if (task.status === "failed") {
      summary = App.esc(STOP_TEXT[task.stop_reason] || "采集失败");
    } else {
      summary = "新增 <b>" + (task.new_count || 0) + "</b> 条商机";
      if (task.dup_count) summary += "，" + task.dup_count + " 条与已有重复";
    }

    let html = '<div class="task-row">'
      + '<span class="t">' + App.esc(humanTime(task.started_at)) + "</span>"
      + "<span>" + App.esc(areaLabel(task)) + "</span>"
      + '<span class="badge ' + meta[1] + '">' + meta[0] + "</span>"
      + "<span>" + summary + "</span>"
      + '<span class="meta ms-auto">' + App.esc(siteNameOf(task)) + "</span>"
      // 每条记录都能一键跳到工作台看这批商机，不必再去两个下拉里挑
      + '<button type="button" class="btn btn-sm btn-link py-0 task-goto"'
      + ' data-province="' + App.esc(task.province) + '"'
      + ' data-city="' + App.esc(task.city) + '">查看商机</button>'
      + "</div>";

    // 失败任务把原因直接带出来，不用再点一层
    const detail = Array.isArray(task.fail_detail) ? task.fail_detail : [];
    if (detail.length && task.status !== "running") {
      html += '<div class="task-detail">' + detail.slice(0, 3).map(function (row) {
        return "· " + App.esc(row.title || row.url || "未知公告") + "：" + App.esc(row.reason || "");
      }).join("<br>") + "</div>";
    }
    return html;
  }

  async function loadHistory(resume) {
    try {
      const tasks = await jsonOrThrow("/crawl/tasks?limit=30");
      historyEl.innerHTML = tasks.length
        ? tasks.map(historyRow).join("")
        : '<div class="empty-tip">还没有采集记录——选一个地区，点「开始采集」。</div>';
      // 刷新页面后若有任务还在跑，接着轮询：不然进度就永远停在那一刻
      if (resume !== false) resumeRunning(tasks);
    } catch (err) {
      if (err.message === "登录已失效") return;
      historyEl.innerHTML = '<div class="empty-tip text-danger">读取采集记录失败：' +
        App.esc(err.message) + "</div>";
    }
  }

  function resumeRunning(tasks) {
    if (polling) return;
    const running = (tasks || []).find(function (t) { return t.status === "running"; });
    if (!running) return;
    progressEl.classList.remove("d-none");
    barPct = 2;
    renderTask(running);
    lockStart("采集中...");
    polling = true;
    pollTask(running.id);
  }

  function loadTaskPage() {
    loadRegions();
    loadHistory();
  }

  regionSelect.addEventListener("change", renderRegionInfo);
  startBtn.addEventListener("click", startCrawl);
  gotoBtn.addEventListener("click", function () {
    goToRegion(lastArea);
  });
  // 采集记录行由 innerHTML 反复重建，按钮统一走事件委托
  historyEl.addEventListener("click", function (event) {
    const btn = event.target.closest(".task-goto");
    if (!btn) return;
    goToRegion({ province: btn.dataset.province, city: btn.dataset.city });
  });

  // ------------------------------------------------------------------
  // 站点管理页：识别（只需 URL）+ 站点与地区
  // ------------------------------------------------------------------
  const probeAlert = $("probeAlert");
  const probeUrl = $("probeListUrl");
  const probeRunBtn = $("probeRun");
  const probeStep1 = $("probeStep1");
  const probeStep2 = $("probeStep2");
  const probeStep3 = $("probeStep3");
  const probeSiteNameEl = $("probeSiteName");
  const probeSummaryEl = $("probeSummary");
  const probeJsonEl = $("probeJson");
  const regProvince = $("regProvince");
  const regCity = $("regCity");
  const regSaveBtn = $("regSave");
  const siteListEl = $("siteList");

  // 识别成功后就地登记地区用；只存在内存，刷新页面重来一次即可
  let probedSite = null;
  let sites = [];

  function resetProbeFlow() {
    probedSite = null;
    probeStep2.classList.add("d-none");
    probeStep3.classList.add("d-none");
    probeStep1.classList.remove("d-none");
    regProvince.value = "";
    regCity.value = "";
    regProvince.classList.remove("is-invalid");
    regCity.classList.remove("is-invalid");
  }

  async function runProbe() {
    const url = probeUrl.value.trim();
    if (!url) {
      probeUrl.classList.add("is-invalid");
      showValid("请先粘贴公告列表页的网址");
      return;
    }
    let parsed;
    try {
      parsed = new URL(url);
    } catch (err) {
      probeUrl.classList.add("is-invalid");
      showValid("网址格式不对，需要以 http:// 或 https:// 开头");
      return;
    }
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      probeUrl.classList.add("is-invalid");
      showValid("网址需要以 http:// 或 https:// 开头");
      return;
    }
    probeUrl.classList.remove("is-invalid");

    hideAlert(probeAlert);
    probeStep1.classList.add("d-none");
    probeStep3.classList.add("d-none");
    probeStep2.classList.remove("d-none");
    probeRunBtn.disabled = true;

    try {
      // 站点编码 / 名称都不传：编码按域名自动生成，名称由模型从页面推断
      const res = await App.postForm("/crawl/probe", { list_url: url });
      if (res.code === 401) {
        location.href = "/login";
        return;
      }
      if (res.code !== 0) throw new Error(res.msg || "识别失败");

      const data = res.data || {};
      const template = data.template || {};
      const evidence = data.evidence || {};

      probedSite = {
        id: data.site_id,
        name: data.site_name || data.site_code,
        code: data.site_code,
      };
      probeSiteNameEl.textContent = probedSite.name;
      probeSummaryEl.textContent = "找到 " + (evidence.list_items || 0) +
        " 条公告，正文内容读取正常，可以开始采集。";
      // 选择器 / 翻页规则对用户没意义，收进折叠区给排查用
      probeJsonEl.textContent = JSON.stringify({
        site_code: data.site_code,
        selectors: template.selectors || {},
        pagination: template.pagination || {},
      }, null, 2);

      probeStep2.classList.add("d-none");
      probeStep3.classList.remove("d-none");
      regProvince.focus();
      loadSiteList();
    } catch (err) {
      if (err.message === "登录已失效") return;
      probeStep2.classList.add("d-none");
      probeStep1.classList.remove("d-none");
      showAlert(probeAlert, "识别失败：" + err.message, "danger");
    } finally {
      probeRunBtn.disabled = false;
    }
  }

  async function saveRegion() {
    if (!probedSite) {
      showAlert(probeAlert, "请先识别一个网站。", "warning");
      return;
    }
    const province = regProvince.value.trim();
    const city = regCity.value.trim();
    const missProvince = !province;
    const missCity = !city;
    regProvince.closest(".field").classList.toggle("has-error", missProvince);
    regCity.closest(".field").classList.toggle("has-error", missCity);
    regProvince.classList.toggle("is-invalid", missProvince);
    regCity.classList.toggle("is-invalid", missCity);
    if (missProvince || missCity) {
      showValid(missProvince && missCity ? "请填写省份和城市"
        : missProvince ? "请填写省份" : "请填写城市");
      return;
    }

    regSaveBtn.disabled = true;
    try {
      // 入口地址不用传：后端从站点配方的翻页模板反推（用户不该被要求知道它）
      const res = await App.postForm("/crawl/regions", {
        site_id: probedSite.id,
        province: province,
        city: city,
      });
      if (res.code === 401) {
        location.href = "/login";
        return;
      }
      if (res.code !== 0) throw new Error(res.msg || "保存失败");
      const label = province === city ? city : province + " · " + city;
      showAlert(probeAlert, "已开通「" + label + "」的采集，可在「采集任务」页发起采集。", "success");
      probeUrl.value = "";
      resetProbeFlow();
      loadSiteList();
    } catch (err) {
      if (err.message === "登录已失效") return;
      showAlert(probeAlert, "保存失败：" + err.message, "danger");
    } finally {
      regSaveBtn.disabled = false;
    }
  }

  function addRegionFormHTML(siteId) {
    return '<div class="add-region d-none" data-add-form="' + siteId + '">'
      + '<div class="form-row">'
      + '<div class="field"><label class="field-label req">省份</label>'
      + '<input class="form-control ar-province" placeholder="如：安徽省">'
      + '<div class="field-error">请填写省份</div></div>'
      + '<div class="field"><label class="field-label req">城市</label>'
      + '<input class="form-control ar-city" placeholder="如：芜湖市">'
      + '<div class="field-error">请填写城市</div></div>'
      + '<button type="button" class="btn btn-primary ar-save" style="min-width:110px">保存</button>'
      + '<button type="button" class="btn btn-outline-secondary ar-cancel">取消</button>'
      + "</div></div>";
  }

  function siteCard(site, siteRegions) {
    const name = site.site_name || site.site_code;
    // 站点级「最近采集」= 其下地区里最晚的一次；一个地区都没有就写从未
    const lastCrawl = siteRegions.reduce(function (acc, region) {
      if (!region.last_crawl_at) return acc;
      return (!acc || String(region.last_crawl_at) > String(acc)) ? region.last_crawl_at : acc;
    }, "");

    const chips = siteRegions.map(function (region) {
      const label = areaLabel(region);
      return '<span class="region-chip">' + App.esc(label)
        + ' <button type="button" class="chip-x" title="删除该地区"'
        + ' data-del-region="' + region.id + '"'
        + ' data-label="' + App.esc(label) + '">×</button></span>';
    }).join("");

    return '<div class="site-card" data-site="' + site.id + '">'
      + '<div class="d-flex align-items-center gap-3 flex-wrap">'
      + '<span class="site-name">' + App.esc(name) + "</span>"
      + (chips || '<span class="meta">还没有地区</span>')
      + '<span class="meta">最近采集：' + (lastCrawl ? App.esc(humanTime(lastCrawl)) : "从未") + "</span>"
      + '<span class="ms-auto d-flex gap-2 align-items-center">'
      + '<button type="button" class="btn btn-sm btn-outline-primary" data-add-region="' + site.id + '">添加地区</button>'
      + '<button type="button" class="btn btn-sm btn-outline-danger" data-del-site="' + site.id + '"'
      + ' data-name="' + App.esc(name) + '">删除</button>'
      + "</span></div>"
      + addRegionFormHTML(site.id)
      + "</div>";
  }

  async function doDelete(url, doneMessage) {
    try {
      const res = await App.request(url, "DELETE");
      if (res.code === 401) {
        location.href = "/login";
        return;
      }
      if (res.code === 403) throw new Error("需要管理员权限");
      if (res.code !== 0) throw new Error(res.msg || "删除失败");
      showAlert(probeAlert, (res.msg || doneMessage) + "。", "success");
      await loadSiteList();
      // 地区没了，采集任务页的下拉必须跟着变，否则还能选到一个已删的地区
      await loadRegions();
    } catch (err) {
      if (err.message === "登录已失效") return;
      showAlert(probeAlert, "删除失败：" + err.message, "danger");
    }
  }

  function bindAddRegionForm(form, siteId) {
    const provinceInput = form.querySelector(".ar-province");
    const cityInput = form.querySelector(".ar-city");
    clearErrorOnInput(provinceInput);
    clearErrorOnInput(cityInput);

    form.querySelector(".ar-cancel").addEventListener("click", function () {
      form.classList.add("d-none");
    });

    form.querySelector(".ar-save").addEventListener("click", async function () {
      const province = provinceInput.value.trim();
      const city = cityInput.value.trim();
      const missProvince = !province;
      const missCity = !city;
      provinceInput.closest(".field").classList.toggle("has-error", missProvince);
      cityInput.closest(".field").classList.toggle("has-error", missCity);
      provinceInput.classList.toggle("is-invalid", missProvince);
      cityInput.classList.toggle("is-invalid", missCity);
      if (missProvince || missCity) {
        showValid(missProvince && missCity ? "请填写省份和城市"
          : missProvince ? "请填写省份" : "请填写城市");
        return;
      }
      try {
        const res = await App.postForm("/crawl/regions", {
          site_id: siteId,
          province: province,
          city: city,
        });
        if (res.code === 401) {
          location.href = "/login";
          return;
        }
        if (res.code !== 0) throw new Error(res.msg || "保存失败");
        showAlert(probeAlert, "已开通「" + (province === city ? city : province + " · " + city) +
          "」的采集。", "success");
        await loadSiteList();
        await loadRegions();
      } catch (err) {
        if (err.message === "登录已失效") return;
        showAlert(probeAlert, "保存失败：" + err.message, "danger");
      }
    });
  }

  function bindSiteCardEvents() {
    siteListEl.querySelectorAll("[data-add-region]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const form = siteListEl.querySelector('[data-add-form="' + btn.dataset.addRegion + '"]');
        if (!form) return;
        form.classList.toggle("d-none");
        const first = form.querySelector(".ar-province");
        if (!form.classList.contains("d-none") && first) first.focus();
      });
    });

    siteListEl.querySelectorAll("[data-add-form]").forEach(function (form) {
      bindAddRegionForm(form, form.dataset.addForm);
    });

    siteListEl.querySelectorAll("[data-del-site]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        askConfirm(
          "确定删除「" + btn.dataset.name + "」？",
          "该站点下的地区会一并移除，之后不能再采集；已入库的商机不受影响。",
          function () { doDelete("/crawl/sites/" + btn.dataset.delSite, "站点已删除"); }
        );
      });
    });

    siteListEl.querySelectorAll("[data-del-region]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        askConfirm(
          "确定删除地区「" + btn.dataset.label + "」？",
          "删除后该地区不能再采集；已入库的商机不受影响。",
          function () { doDelete("/crawl/regions/" + btn.dataset.delRegion, "采集地区已删除"); }
        );
      });
    });
  }

  async function loadSiteList() {
    try {
      const [siteRows, regionRows] = await Promise.all([
        jsonOrThrow("/crawl/sites"),
        jsonOrThrow("/crawl/regions"),
      ]);
      sites = siteRows || [];
      const bySite = {};
      (regionRows || []).forEach(function (region) {
        (bySite[region.site_id] = bySite[region.site_id] || []).push(region);
      });
      siteListEl.innerHTML = sites.length
        ? sites.map(function (site) { return siteCard(site, bySite[site.id] || []); }).join("")
        : '<div class="empty-tip">还没有接入任何网站——粘贴一个公告列表页的网址，识别通过即可开通采集。</div>';
      bindSiteCardEvents();
    } catch (err) {
      if (err.message === "登录已失效") return;
      siteListEl.innerHTML = '<div class="empty-tip text-danger">读取站点失败：' +
        App.esc(err.message) + "</div>";
    }
  }

  probeRunBtn.addEventListener("click", runProbe);
  regSaveBtn.addEventListener("click", saveRegion);
  probeUrl.addEventListener("keydown", function (event) {
    if (event.key === "Enter") runProbe();
  });
  clearErrorOnInput(probeUrl);
  clearErrorOnInput(regProvince);
  clearErrorOnInput(regCity);

  // ------------------------------------------------------------------
  // 角色：站点管理页签只对 admin 显示
  // ------------------------------------------------------------------
  async function loadRole() {
    try {
      const res = await App.fetchJson("/user/me");
      if (res.code === 401) {
        location.href = "/login";
        return;
      }
      role = (res.code === 0 && res.data && res.data.role) || "";
      $("tabSite").classList.toggle("d-none", role !== "admin");
    } catch (err) {
      // 角色判断失败不影响采集主流程，静默即可（后端仍会拦）
    }
  }

  (async function init() {
    await loadRole();
    // 先备好地区下拉：用户第一眼可能就点「采集任务」
    await loadRegions();
  })();
})();
