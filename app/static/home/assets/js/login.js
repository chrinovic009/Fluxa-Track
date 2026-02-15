const togglePassword = document.getElementById("togglePassword");
const passwordInput = document.getElementById("password");

togglePassword.addEventListener("click", () => {
  const type = passwordInput.getAttribute("type");

  if (type === "password") {
    passwordInput.setAttribute("type", "text");
    togglePassword.textContent = "🙈";
  } else {
    passwordInput.setAttribute("type", "password");
    togglePassword.textContent = "👁";
  }
});
