document.addEventListener("DOMContentLoaded", () => {
  const notif = document.querySelector(".notification-card");
  notif.style.opacity = 0;
  notif.style.transform = "translateY(20px)";
  
  setTimeout(() => {
    notif.style.transition = "all 0.6s ease";
    notif.style.opacity = 1;
    notif.style.transform = "translateY(0)";
  }, 300);

  // Gestion du modale
  const viewBtn = document.getElementById("viewReportBtn");
  const modal = document.getElementById("reportModal");
  const closeBtns = document.querySelectorAll(".close-modal");

  viewBtn.addEventListener("click", () => {
    modal.style.display = "flex";
  });

  closeBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      modal.style.display = "none";
    });
  });

  // Fermer si clic en dehors
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.style.display = "none";
    }
  });
});
