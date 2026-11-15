/* 商机地图：地图初始化、点位渲染、七页签 InfoWindow、筛选。
 * 通过 window.MapPage.refresh 暴露刷新能力，采集完成后由 source.js 调用。
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
  const resetBtn = document.getElementById("filterReset");
  const visibleEl = document.getElementById("visibleCount");

  const PIN_CLASS = { "高": "high", "中": "mid", "低": "low" };

  function showLoading(show) {
    loadingEl.classList.toggle("d-none", !show);
  }

  function showNotice(message) {
    noticeEl.textContent = message || "";
    noticeEl.classList.toggle("d-none", !message);
  }

  if (!window.AMap) {
    showNotice("高德 JS API 未加载，请在 .env 配置 AMAP_JS_KEY（Web端 JS API key）。");
    return;
  }

  // 默认中心南京；只创建一个 InfoWindow 实例，点击不同水滴时整体替换内容
  const map = new AMap.Map("map", {
    zoom: 11,
    center: [118.796877, 32.060255],
    viewMode: "2D",
  });
  const infoWindow = new AMap.InfoWindow({ offset: new AMap.Pixel(0, -34) });
  let allPoints = [];
  let markers = [];

  function detailHtml(point) {
    const rows = [
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

    const body = rows.map(([label, value]) =>
      `<div class="lead-iw-row"><div class="lead-iw-label">${label}</div>` +
      `<div class="lead-iw-value">${esc(value)}</div></div>`
    ).join("");

    const sourceLink = point.source_url
      ? `<a class="d-inline-block mt-2 small" href="${esc(point.source_url)}" ` +
        `target="_blank" rel="noopener noreferrer">查看原文</a>`
      : "";

    // 页签 ID 是全局唯一的：当前只有一个 InfoWindow，setContent 会整体替换，
    // 固定 ID 不会冲突。每个 pane 的 data-lead-id 是其它 JS 模块的挂载契约。
    return `
      <div class="lead-iw">
        <h6 class="fw-bold mb-2">${esc(point.project_name)}</h6>

        <ul class="nav nav-tabs nav-fill lead-tabs" role="tablist">
          <li class="nav-item" role="presentation">
            <button class="nav-link active" type="button" role="tab"
                    data-bs-toggle="tab" data-bs-target="#iwChat">概况</button>
          </li>
          <li class="nav-item" role="presentation">
            <button class="nav-link" type="button" role="tab"
                    data-bs-toggle="tab" data-bs-target="#iwLead">商机</button>
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
                    data-bs-toggle="tab" data-bs-target="#iwSummary">总结</button>
          </li>
        </ul>

        <div class="tab-content lead-tab-content pt-2">
          <div class="tab-pane fade show active" id="iwChat" role="tabpanel"
               data-lead-id="${point.id}"></div>

          <div class="tab-pane fade" id="iwLead" role="tabpanel">
            ${body}${sourceLink}
          </div>

          <div class="tab-pane fade" id="iwOwner" role="tabpanel"
               data-lead-id="${point.id}"></div>

          <div class="tab-pane fade" id="iwFollow" role="tabpanel" data-lead-id="${point.id}"></div>

          <div class="tab-pane fade" id="iwBid" role="tabpanel"
               data-lead-id="${point.id}" data-group="bidding"></div>

          <div class="tab-pane fade" id="iwInit" role="tabpanel"
               data-lead-id="${point.id}" data-group="initiation"></div>

          <div class="tab-pane fade" id="iwSummary" role="tabpanel"
               data-lead-id="${point.id}"></div>
        </div>
      </div>`;
  }

  function addMarker(point) {
    // 意向等级映射到水滴颜色；未知等级按“中”处理
    const pinClass = PIN_CLASS[point.intent_level] || "mid";
    const content =
      `<div class="lead-marker" title="${esc(point.project_name)}">` +
      `<div class="lead-pin ${pinClass}"></div>` +
      `<div class="lead-name">${esc(point.project_name)}</div>` +
      `</div>`;

    const marker = new AMap.Marker({
      // 接口返回的经纬度可能是字符串，统一转 Number；offset 与 CSS 水滴尺寸匹配
      position: [Number(point.longitude), Number(point.latitude)],
      content,
      offset: new AMap.Pixel(-11, -24),
      map,
    });

    marker.on("click", function () {
      infoWindow.setContent(detailHtml(point));
      infoWindow.open(map, marker.getPosition());
      // 概况是默认页签，不会触发 shown.bs.tab，必须在这里显式初始化聊天
      if (window.ChatPage) {
        window.ChatPage.init(point.id);
      }
    });
    return marker;
  }

  function regionOf(point) {
    return point.province || point.city || "未标注";
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

  // 每次筛选都先移除旧 marker，再按条件重建；缺失行业/区域按“未标注”处理
  function applyFilters() {
    const industry = industryEl.value;
    const intent = intentEl.value;
    const region = regionEl.value;

    const filtered = allPoints.filter(function (point) {
      if (industry && (point.industry || "未标注") !== industry) return false;
      if (intent && point.intent_level !== intent) return false;
      if (region && regionOf(point) !== region) return false;
      return true;
    });

    if (markers.length) {
      map.remove(markers);
      markers = [];
    }
    visibleEl.textContent = filtered.length;

    if (!filtered.length) {
      showNotice(
        allPoints.length
          ? "当前筛选条件下没有商机。"
          : "暂无可展示的商机点位，请先采集商机并确保经纬度解析成功。"
      );
      return;
    }
    showNotice("");
    markers = filtered.map(addMarker);
    map.setFitView(markers, false, [80, 80, 80, 80]);
  }

  // 拉取全部点位后重建筛选选项；401 说明会话失效，直接回登录页
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
      applyFilters();
    } catch (err) {
      showNotice("加载商机失败：" + err.message);
    } finally {
      showLoading(false);
    }
  }

  // source.js 在执行采集成功后调用 MapPage.refresh() 刷新点位
  window.MapPage = { refresh: load };
  refreshBtn.addEventListener("click", load);
  [industryEl, intentEl, regionEl].forEach(function (el) {
    el.addEventListener("change", applyFilters);
  });
  resetBtn.addEventListener("click", function () {
    industryEl.value = "";
    intentEl.value = "";
    regionEl.value = "";
    applyFilters();
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
