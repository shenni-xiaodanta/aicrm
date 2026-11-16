/* 商机工作台：列表/地图双视图共享筛选、AMap 点位渲染、右侧抽屉七页签。
 * 通过 window.MapPage.refresh 暴露刷新能力，采集完成后由 source.js 调用。
 *
 * 抽屉沿用 InfoWindow 时代的挂载契约（各模块零改动）：
 *   - 页签 pane 用固定 ID（iwLead/iwOwner/iwFollow/iwBid/iwInit/iwChat/iwSummary），
 *     模块靠 document 级 shown.bs.tab 事件懒加载，按 pane 的 data-lead-id 取商机
 *   - 每次打开抽屉整体重建内容子树（与原来 InfoWindow setContent 整体替换一致），
 *     模块通过「pane 元素引用 / initialized 标记」感知新 DOM 并重新挂载
 */
(function () {
  "use strict";

  const { esc, fetchJson, postJson } = window.App;
  const countEl = document.getElementById("count");
  const loadingEl = document.getElementById("loading");
  const noticeEl = document.getElementById("notice");
  const refreshBtn = document.getElementById("refresh");
  const logoutBtn = document.getElementById("logout");
  const industryEl = document.getElementById("filterIndustry");
  const intentEl = document.getElementById("filterIntent");
  const regionEl = document.getElementById("filterRegion");
  const kwEl = document.getElementById("filterKeyword");
  const resetBtn = document.getElementById("filterReset");
  const visibleEl = document.getElementById("visibleCount");
  const paneList = document.getElementById("viewList");
  const paneMap = document.getElementById("map");
  const tbodyEl = document.getElementById("leadTbody");
  const statusTotalEl = document.getElementById("statusTotal");
  const statusGeoEl = document.getElementById("statusGeo");
  const drawerEl = document.getElementById("drawer");
  const drawerContentEl = document.getElementById("drawerContent");

  const PIN_CLASS = { "高": "high", "中": "mid", "低": "low" };

  const state = {
    view: "table",   // table | map；默认列表，地图首次切换时才初始化
    industry: "",
    intent: "",
    region: "",
    kw: "",
    sortKey: "id",   // id（采集时间）| budget | date
    sortDesc: true,
    selId: null,     // 当前抽屉打开的商机，列表行高亮用
  };

  let allPoints = [];
  let markers = [];
  let map = null;  // 惰性创建：AMap 在 display:none 的容器里初始化会拿到 0 尺寸

  function showLoading(show) {
    loadingEl.classList.toggle("d-none", !show);
  }

  function showNotice(message) {
    noticeEl.textContent = message || "";
    noticeEl.classList.toggle("d-none", !message);
  }

  function ensureMap() {
    if (map || !window.AMap) return;
    if (!window.AMap) return;
    // 默认中心南京；地图实例全局只有一个
    map = new AMap.Map("map", {
      zoom: 11,
      center: [118.796877, 32.060255],
      viewMode: "2D",
    });
  }

  // 预算库里可能是数字也可能是「187.83万元」这类文本，统一抠出数值用于排序
  function budgetNum(point) {
    const n = Number(String(point.budget == null ? "" : point.budget).replace(/[^\d.]/g, ""));
    return Number.isFinite(n) ? n : 0;
  }

  function regionOf(point) {
    return point.province || point.city || "未标注";
  }

  function titleOf(point) {
    // 老数据里可能残留 project_name 字段名，兜底取 source_title
    return point.source_title || point.project_name || "（无标题）";
  }

  function hasGeo(point) {
    return Number(point.longitude) > 0 && Number(point.latitude) > 0;
  }

  function uniqueValues(values) {
    return Array.from(new Set(values.filter(Boolean))).sort();
  }

  // 保留第一个“全部…”选项，并在可能时恢复之前的选择
  function fillSelect(select, values) {
    const current = select.value;
    const allOption = select.options[0].outerHTML;
    select.innerHTML = allOption;
    values.forEach(function (value) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    });
    select.value = values.indexOf(current) >= 0 ? current : "";
  }

  function intentBadge(value) {
    const cls = { "高": "text-bg-danger", "中": "text-bg-primary", "低": "text-bg-secondary" };
    if (!value) return '<span class="badge text-bg-light">未标注</span>';
    return `<span class="badge rounded-pill ${cls[value] || "text-bg-secondary"}">${esc(value)}</span>`;
  }

  function filtered() {
    const kw = state.kw.toLowerCase();
    const rows = allPoints.filter(function (point) {
      if (state.industry && (point.industry || "未标注") !== state.industry) return false;
      if (state.intent && point.intent_level !== state.intent) return false;
      if (state.region && regionOf(point) !== state.region) return false;
      if (kw) {
        const hay = [
          titleOf(point), point.customer, point.project_summary, point.project_address,
        ].join(" ").toLowerCase();
        if (hay.indexOf(kw) < 0) return false;
      }
      return true;
    });

    // 排序在客户端做：一页数据量在千级以内，没必要为排序加后端参数
    rows.sort(function (a, b) {
      let x, y;
      if (state.sortKey === "budget") {
        x = budgetNum(a); y = budgetNum(b);
      } else if (state.sortKey === "date") {
        x = a.publish_date || ""; y = b.publish_date || "";
      } else {
        x = a.id; y = b.id;
      }
      if (x < y) return state.sortDesc ? 1 : -1;
      if (x > y) return state.sortDesc ? -1 : 1;
      return 0;
    });
    return rows;
  }

  function renderTable(rows) {
    const html = rows.map(function (point) {
      return `<tr data-id="${point.id}" class="${state.selId === point.id ? "sel" : ""}">
        <td><span class="wb-title" title="${esc(titleOf(point))}">${esc(titleOf(point))}</span>
            <span class="wb-sub">${esc(point.customer)} · ${esc(point.publish_date)}</span></td>
        <td>${esc(regionOf(point))}</td>
        <td>${esc(point.industry || "未标注")}</td>
        <td class="wb-budget">${esc(point.budget)}</td>
        <td>${intentBadge(point.intent_level)}</td>
        <td>${esc(point.contact)}</td>
        <td class="wb-muted">${hasGeo(point) ? "有坐标" : "无坐标"}</td>
      </tr>`;
    }).join("");
    tbodyEl.innerHTML = html
      || '<tr><td colspan="7" class="wb-empty">没有符合条件的商机</td></tr>';
  }

  function addMarker(point) {
    // 意向等级映射到水滴颜色；未知等级按“中”处理
    const pinClass = PIN_CLASS[point.intent_level] || "mid";
    const content =
      `<div class="lead-marker" title="${esc(titleOf(point))}">` +
      `<div class="lead-pin ${pinClass}"></div>` +
      `<div class="lead-name">${esc(titleOf(point))}</div>` +
      `</div>`;

    const marker = new AMap.Marker({
      // 接口返回的经纬度可能是字符串，统一转 Number；offset 与 CSS 水滴尺寸匹配
      position: [Number(point.longitude), Number(point.latitude)],
      content,
      offset: new AMap.Pixel(-11, -24),
      map,
    });

    // 点击水滴不再用 InfoWindow，改开右侧抽屉——列表和地图共用同一套页签
    marker.on("click", function () {
      openDrawer(point);
    });
    return marker;
  }

  // 每次筛选都先移除旧 marker，再按条件重建；无坐标商机不进地图
  function renderMap(rows) {
    if (!map) return;
    if (markers.length) {
      map.remove(markers);
      markers = [];
    }
    const geo = rows.filter(hasGeo);
    if (!geo.length) return;
    markers = geo.map(addMarker);
    map.setFitView(markers, false, [80, 80, 80, 80]);
  }

  function render() {
    const rows = filtered();
    const geoCount = rows.filter(hasGeo).length;

    renderTable(rows);
    renderMap(rows);

    visibleEl.textContent = rows.length;
    statusTotalEl.textContent = rows.length;
    statusGeoEl.textContent = geoCount;

    if (!allPoints.length) {
      showNotice("暂无可展示的商机，请先采集商机并确保经纬度解析成功。");
    } else if (!rows.length) {
      showNotice("当前筛选条件下没有商机。");
    } else {
      showNotice("");
    }
  }

  // ---------------------------------------------------------------------
  // 右侧抽屉
  // ---------------------------------------------------------------------
  function drawerHtml(point) {
    const fields = [
      ["客户", point.customer],
      ["行业", point.industry],
      ["意向", point.intent_level],
      ["预算", point.budget],
      ["地址", point.project_address],
      ["地区", [point.province, point.city].filter(Boolean).join(" / ")],
      ["联系", point.contact],
      ["需求", (point.needs || []).join("；")],
      ["风险", (point.objections || []).join("；")],
      ["下一步", point.next_action],
      ["概述", point.project_summary],
      ["发布", point.publish_date],
    ].filter(([, value]) => value && String(value).trim());

    const body = fields.map(([label, value]) =>
      `<div class="lead-iw-row"><div class="lead-iw-label">${label}</div>` +
      `<div class="lead-iw-value">${esc(value)}</div></div>`
    ).join("");

    const sourceLink = point.source_url
      ? `<a href="${esc(point.source_url)}" target="_blank" rel="noopener noreferrer">查看原文</a>`
      : '<span class="text-muted">无原文链接</span>';
    const footSource = point.source_url
      ? `<a href="${esc(point.source_url)}" target="_blank" rel="noopener noreferrer">打开原站</a>`
      : '<span class="text-muted small">无原文链接</span>';

    // 页签 ID 是全局唯一的：当前只有一个抽屉，drawerContent 每次整体重建，
    // 固定 ID 不会冲突。每个 pane 的 data-lead-id 是其它 JS 模块的挂载契约。
    // 页签顺序与名称对齐原项目：概况 / 负责人 / 跟进 / 招投标 / 立项 / 问答 / 总结。
    return `
      <div class="lead-iw wb-inner d-flex flex-column h-100">
        <div class="wb-head">
          <button type="button" class="wb-close" data-drawer-close aria-label="关闭">×</button>
          <h6 class="fw-bold mb-2 wb-dw-title">${esc(titleOf(point))}</h6>
          <div class="wb-meta">
            <span class="badge text-bg-primary">${esc(regionOf(point))}</span>
            ${intentBadge(point.intent_level)}
            <span class="wb-budget-tag">${esc(point.budget)}</span>
            <span class="text-muted">发布 ${esc(point.publish_date)}</span>
          </div>
          <ul class="nav nav-tabs nav-fill lead-tabs" role="tablist">
            <li class="nav-item" role="presentation">
              <button class="nav-link active" type="button" role="tab"
                      data-bs-toggle="tab" data-bs-target="#iwLead">概况</button>
            </li>
            <li class="nav-item" role="presentation">
              <button class="nav-link" type="button" role="tab"
                      data-bs-toggle="tab" data-bs-target="#iwOwner">负责人</button>
            </li>
            <li class="nav-item" role="presentation">
              <button class="nav-link" type="button" role="tab"
                      data-bs-toggle="tab" data-bs-target="#iwFollow">跟进</button>
            </li>
            <li class="nav-item" role="presentation">
              <button class="nav-link" type="button" role="tab"
                      data-bs-toggle="tab" data-bs-target="#iwBid">招投标</button>
            </li>
            <li class="nav-item" role="presentation">
              <button class="nav-link" type="button" role="tab"
                      data-bs-toggle="tab" data-bs-target="#iwInit">立项</button>
            </li>
            <li class="nav-item" role="presentation">
              <button class="nav-link" type="button" role="tab"
                      data-bs-toggle="tab" data-bs-target="#iwChat">问答</button>
            </li>
            <li class="nav-item" role="presentation">
              <button class="nav-link" type="button" role="tab"
                      data-bs-toggle="tab" data-bs-target="#iwSummary">总结</button>
            </li>
          </ul>
        </div>

        <div class="tab-content lead-tab-content wb-tab-content flex-grow-1">
          <div class="tab-pane fade show active" id="iwLead" role="tabpanel">
            ${body}<div class="mt-2">${sourceLink}</div>
          </div>

          <div class="tab-pane fade" id="iwOwner" role="tabpanel"
               data-lead-id="${point.id}"></div>

          <div class="tab-pane fade" id="iwFollow" role="tabpanel" data-lead-id="${point.id}"></div>

          <div class="tab-pane fade" id="iwBid" role="tabpanel"
               data-lead-id="${point.id}" data-group="bidding"></div>

          <div class="tab-pane fade" id="iwInit" role="tabpanel"
               data-lead-id="${point.id}" data-group="initiation"></div>

          <div class="tab-pane fade" id="iwChat" role="tabpanel"
               data-lead-id="${point.id}"></div>

          <div class="tab-pane fade" id="iwSummary" role="tabpanel"
               data-lead-id="${point.id}"></div>
        </div>

        <div class="wb-foot">
          ${footSource}
          <button type="button" class="btn btn-sm btn-outline-secondary ms-auto" data-drawer-close>关闭</button>
        </div>
      </div>`;
  }

  function openDrawer(point) {
    state.selId = point.id;
    drawerContentEl.innerHTML = drawerHtml(point);
    drawerEl.classList.add("open");
    drawerEl.setAttribute("aria-hidden", "false");
    // 概况是默认页签，不会触发 shown.bs.tab，问答在这里显式初始化
    if (window.ChatPage) {
      window.ChatPage.init(point.id);
    }
    renderTable(filtered());
  }

  function closeDrawer() {
    drawerEl.classList.remove("open");
    drawerEl.setAttribute("aria-hidden", "true");
    // 内容子树整体清空：模块持有旧 pane 引用时，靠「元素引用变化」重建骨架
    drawerContentEl.innerHTML = "";
    state.selId = null;
    renderTable(filtered());
  }

  // 关闭按钮在重建的内容里，走事件委托绑定
  drawerEl.addEventListener("click", function (event) {
    if (event.target.closest("[data-drawer-close]")) {
      closeDrawer();
    }
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && drawerEl.classList.contains("open")) {
      closeDrawer();
    }
  });

  // 列表行点击开抽屉（事件委托，行会被反复重建）
  tbodyEl.addEventListener("click", function (event) {
    const tr = event.target.closest("tr[data-id]");
    if (!tr) return;
    const id = Number(tr.dataset.id);
    const point = allPoints.find(function (p) { return p.id === id; });
    if (point) openDrawer(point);
  });

  // ---------------------------------------------------------------------
  // 视图切换 / 筛选 / 加载
  // ---------------------------------------------------------------------
  document.querySelectorAll("#viewSeg .seg").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll("#viewSeg .seg").forEach(function (x) {
        x.classList.toggle("active", x === btn);
      });
      state.view = btn.dataset.view;
      paneList.classList.toggle("d-none", state.view !== "table");
      paneMap.classList.toggle("d-none", state.view !== "map");
      if (state.view === "map") {
        ensureMap();
        if (map) {
          // 容器从隐藏变可见后尺寸才确定，让 AMap 重算画布再落点
          map.resize();
          renderMap(filtered());
        }
      }
    });
  });

  document.querySelectorAll("#leadTable th.sortable").forEach(function (th) {
    th.addEventListener("click", function () {
      if (state.sortKey === th.dataset.sort) {
        state.sortDesc = !state.sortDesc;
      } else {
        state.sortKey = th.dataset.sort;
        state.sortDesc = true;
      }
      document.querySelectorAll("#leadTable th.sortable").forEach(function (x) {
        x.classList.toggle("on", x === th);
        const arrow = x.querySelector(".arrow");
        arrow.textContent = x.classList.contains("on") ? (state.sortDesc ? "↓" : "↑") : "";
      });
      render();
    });
  });

  // 拉取全部商机后重建筛选选项；401 说明会话失效，直接回登录页
  async function load() {
    showLoading(true);
    showNotice("");
    try {
      const res = await fetchJson("/shangji/points");
      if (res && res.code === 401) {
        location.href = "/login";
        return;
      }
      allPoints = (res && res.data) || [];
      countEl.textContent = allPoints.length;

      fillSelect(
        industryEl,
        uniqueValues(allPoints.map(function (p) { return p.industry || "未标注"; }))
      );
      fillSelect(regionEl, uniqueValues(allPoints.map(regionOf)));
      render();
    } catch (err) {
      showNotice("加载商机失败：" + err.message);
    } finally {
      showLoading(false);
    }
  }

  // source.js 在执行采集成功后调用 MapPage.refresh() 刷新数据
  window.MapPage = { refresh: load };
  refreshBtn.addEventListener("click", load);
  [industryEl, intentEl, regionEl].forEach(function (el) {
    el.addEventListener("change", function () {
      state.industry = industryEl.value;
      state.intent = intentEl.value;
      state.region = regionEl.value;
      render();
    });
  });
  kwEl.addEventListener("input", function () {
    state.kw = kwEl.value.trim();
    render();
  });
  resetBtn.addEventListener("click", function () {
    industryEl.value = "";
    intentEl.value = "";
    regionEl.value = "";
    kwEl.value = "";
    state.industry = state.intent = state.region = state.kw = "";
    render();
  });
  logoutBtn.addEventListener("click", async function () {
    try {
      await postJson("/user/logout", {});
    } catch (err) {
      /* 忽略退出接口异常，直接回登录页 */
    }
    location.href = "/login";
  });
  load();
})();
