/* 商机采集：三级菜单 + 采集弹窗。
 * 目前只内置安徽省、江苏省；菜单、弹窗和采集入口都在这个文件。
 */
(function () {
  "use strict";

  // 省 -> 地级市；新增省份时在这里补充即可
  const PROVINCES = {
    "安徽省": [
      "合肥市", "芜湖市", "蚌埠市", "淮南市", "马鞍山市", "淮北市", "铜陵市",
      "安庆市", "黄山市", "滁州市", "阜阳市", "宿州市", "六安市", "亳州市",
      "池州市", "宣城市",
    ],
    "江苏省": [
      "南京市", "无锡市", "徐州市", "常州市", "苏州市", "南通市", "连云港市",
      "淮安市", "盐城市", "扬州市", "镇江市", "泰州市", "宿迁市",
    ],
  };

  const menuToggle = document.getElementById("crawlMenuToggle");
  const menuEl = document.getElementById("crawlProvinceMenu");
  const modal = new bootstrap.Modal(document.getElementById("crawlModal"));
  const regionEl = document.getElementById("crawlRegion");
  const baseInput = document.getElementById("crawlBaseDomain");
  const urlInput = document.getElementById("crawlListUrl");
  const alertEl = document.getElementById("crawlAlert");
  const resultEl = document.getElementById("crawlResult");
  const saveBtn = document.getElementById("crawlSave");
  const runBtn = document.getElementById("crawlRun");

  let province = "";
  let city = "";

  function showAlert(message, type) {
    alertEl.className = "alert alert-" + type + " py-2 small";
    alertEl.textContent = message;
  }

  function hideAlert() {
    alertEl.className = "alert py-2 small d-none";
  }

  function showResult(message) {
    resultEl.className = "alert alert-success py-2 small";
    resultEl.textContent = message;
  }

  function hideResult() {
    resultEl.className = "alert py-2 small d-none";
  }

  function hideDropdown() {
    bootstrap.Dropdown.getOrCreateInstance(menuToggle).hide();
  }

  // 动态生成省/市二级子菜单。
  // 通过 .open 类控制显隐，配合 map.html 的 data-bs-auto-close="outside"
  // 保证点击菜单内部不会关闭整个下拉。
  function buildMenu() {
    Object.keys(PROVINCES).forEach(function (name) {
      const item = document.createElement("li");
      item.className = "dropdown-submenu";

      const toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "dropdown-item submenu-toggle";
      toggle.textContent = name;
      toggle.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        const isOpen = item.classList.contains("open");
        menuEl.querySelectorAll(".dropdown-submenu.open").forEach(function (el) {
          el.classList.remove("open");
        });
        if (!isOpen) item.classList.add("open");
      });

      const submenu = document.createElement("ul");
      submenu.className = "dropdown-menu submenu";

      PROVINCES[name].forEach(function (cityName) {
        const cityItem = document.createElement("li");
        const cityButton = document.createElement("button");
        cityButton.type = "button";
        cityButton.className = "dropdown-item";
        cityButton.textContent = cityName;
        cityButton.addEventListener("click", function (event) {
          event.preventDefault();
          event.stopPropagation();
          openCity(name, cityName);
        });
        cityItem.appendChild(cityButton);
        submenu.appendChild(cityItem);
      });

      item.appendChild(toggle);
      item.appendChild(submenu);
      menuEl.appendChild(item);
    });
  }

  function parseUrl(value) {
    try {
      return new URL(value);
    } catch (err) {
      return null;
    }
  }

  // “站点根地址”的定义：只有协议 + 域名，路径为 / 或空，且没有查询参数/hash
  function isOrigin(url) {
    return url && (url.pathname === "/" || url.pathname === "") &&
      !url.search && !url.hash;
  }

  // 校验并规范化表单：
  // - base_domain 必须是站点根地址
  // - list_url 必须是带路径的完整列表页
  // - 两者填反时自动交换并回写，避免用户反复提交失败
  function formValues() {
    let baseDomain = baseInput.value.trim().replace(/\/+$/, "");
    let listUrl = urlInput.value.trim();

    if (!baseDomain || !listUrl) {
      showAlert("请填写 base_domain 和 list_url。", "danger");
      return null;
    }
    if (!parseUrl(baseDomain) || !parseUrl(listUrl)) {
      showAlert("请输入合法的 http:// 或 https:// 地址。", "danger");
      return null;
    }

    // 填反时自动交换并回写表单
    if (!isOrigin(parseUrl(baseDomain)) && isOrigin(parseUrl(listUrl))) {
      const temp = baseDomain;
      baseDomain = listUrl.replace(/\/+$/, "");
      listUrl = temp;
      baseInput.value = baseDomain;
      urlInput.value = listUrl;
      showAlert("已自动交换 base_domain 和 list_url。", "info");
    }

    if (!isOrigin(parseUrl(baseDomain))) {
      showAlert("base_domain 只填站点根域名，如 https://ggzy.hefei.gov.cn。", "danger");
      return null;
    }
    if (isOrigin(parseUrl(listUrl))) {
      showAlert("list_url 需要填完整列表页地址，不能只填域名。", "danger");
      return null;
    }
    return { base_domain: baseDomain, list_url: listUrl };
  }

  // 打开某个城市的采集弹窗，并读取该省/市已保存的配置进行回填
  async function openCity(provinceName, cityName) {
    province = provinceName;
    city = cityName;
    hideDropdown();
    regionEl.textContent = provinceName + " / " + cityName;
    baseInput.value = "";
    urlInput.value = "";
    hideAlert();
    hideResult();
    modal.show();

    try {
      const res = await App.fetchJson(
        "/source/get?province=" + encodeURIComponent(provinceName) +
        "&city=" + encodeURIComponent(cityName)
      );
      if (res.code === 401) {
        location.href = "/login";
        return;
      }
      if (res.code === 0 && res.data) {
        baseInput.value = res.data.base_domain || "";
        urlInput.value = res.data.list_url || "";
      }
    } catch (err) {
      showAlert("读取已保存配置失败：" + err.message, "warning");
    }
  }

  // 保存配置；返回 boolean 供 run() 判断是否可以继续执行采集
  async function save() {
    const values = formValues();
    if (!values) return false;

    saveBtn.disabled = true;
    try {
      const res = await App.postJson("/source/save", {
        province: province,
        city: city,
        base_domain: values.base_domain,
        list_url: values.list_url,
      });
      if (res.code === 401) {
        location.href = "/login";
        return false;
      }
      if (res.code === 0) {
        showAlert("保存成功。", "success");
        return true;
      }
      showAlert(res.msg || "保存失败。", "danger");
      return false;
    } catch (err) {
      showAlert("保存失败：" + err.message, "danger");
      return false;
    } finally {
      saveBtn.disabled = false;
    }
  }

  // 执行采集：先保存配置，再调用后端爬取；成功后通知地图刷新点位
  async function run() {
    const values = formValues();
    if (!values) return;

    hideResult();
    // 执行前先保存配置
    if (!(await save())) return;

    runBtn.disabled = true;
    saveBtn.disabled = true;
    runBtn.textContent = "采集中...";
    try {
      const res = await App.postJson("/shangji/crawl", values);
      if (res.code === 401) {
        location.href = "/login";
        return;
      }
      if (res.code === 0 && res.data) {
        const data = res.data;
        showResult(
          "采集完成：共 " + data.total + " 条，新增 " + data.saved +
          " 条，失败 " + data.failed + " 条。"
        );
        if (window.MapPage && window.MapPage.refresh) {
          window.MapPage.refresh();
        }
      } else {
        showAlert(res.msg || "采集失败。", "danger");
      }
    } catch (err) {
      showAlert("采集失败：" + err.message, "danger");
    } finally {
      runBtn.disabled = false;
      saveBtn.disabled = false;
      runBtn.textContent = "执行";
    }
  }

  // 每次重新打开下拉时清掉上次残留的展开状态
  menuToggle.addEventListener("shown.bs.dropdown", function () {
    menuEl.querySelectorAll(".dropdown-submenu.open").forEach(function (el) {
      el.classList.remove("open");
    });
  });

  saveBtn.addEventListener("click", save);
  runBtn.addEventListener("click", run);
  buildMenu();
})();
