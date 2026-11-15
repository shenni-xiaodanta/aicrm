/* 注册页 */
(function () {
  "use strict";

  const form = document.getElementById("registerForm");
  const alertEl = document.getElementById("alert");
  const submitBtn = document.getElementById("submit");

  function showMessage(message) {
    alertEl.className = "alert alert-danger py-2 small";
    alertEl.textContent = message;
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const nickname = document.getElementById("nickname").value.trim();
    const password = document.getElementById("password").value;
    const confirm = document.getElementById("confirm").value;

    if (!username || !password) {
      showMessage("请填写用户名和密码。");
      return;
    }
    if (password.length < 6) {
      showMessage("密码至少 6 位。");
      return;
    }
    if (password !== confirm) {
      showMessage("两次输入的密码不一致。");
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "注册中...";
    try {
      const res = await App.postJson("/user/register", {
        username,
        password,
        nickname,
      });
      if (res.code === 0) {
        location.href = "/login?registered=1";
        return;
      }
      showMessage(res.msg || "注册失败。");
    } catch (err) {
      showMessage("网络异常：" + err.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "注 册";
    }
  });
})();
