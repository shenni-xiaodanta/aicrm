/* 登录页 */
(function () {
  "use strict";

  const form = document.getElementById("loginForm");
  const alertEl = document.getElementById("alert");
  const submitBtn = document.getElementById("submit");

  function showMessage(message, type) {
    alertEl.className = "alert alert-" + type + " py-2 small";
    alertEl.textContent = message;
  }

  if (new URLSearchParams(location.search).get("registered")) {
    showMessage("注册成功，请登录。", "success");
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    if (!username || !password) {
      showMessage("请输入用户名和密码。", "danger");
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "登录中...";
    try {
      const res = await App.postJson("/user/login", { username, password });
      if (res.code === 0) {
        location.href = "/";
        return;
      }
      showMessage(res.msg || "登录失败。", "danger");
    } catch (err) {
      showMessage("网络异常：" + err.message, "danger");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "登 录";
    }
  });
})();
