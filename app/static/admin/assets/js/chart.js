// POUR LES CEO DES ENTREPRIES QUI CREENT LEURS COMPTES, ILS VOIENT UN DASHBOARD AVEC DES CHARTS QUI SE METTENT A JOUR TOUT SEULS

// Revenus par source (bar chart)
let revenueChart = null;

function loadRevenueChart() {
  fetch("/admin/revenue")
    .then(response => response.json())
    .then(chartData => {

      const ctxRevenue = document
        .getElementById("chart-revenue")
        .getContext("2d");

      // First load
      if (!revenueChart) {
        revenueChart = new Chart(ctxRevenue, {
          type: "bar",
          data: {
            labels: chartData.labels,
            datasets: [{
              label: "Revenue",
              backgroundColor: "#000",
              data: chartData.data,
              borderRadius: 4,
              barThickness: "flex"
            }]
          },
          options: {
            responsive: true,
            plugins: {
              legend: { display: false }
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: { color: "#737373" }
              },
              x: {
                ticks: { color: "#737373" }
              }
            }
          }
        });
      } 
      // Update only
      else {
        revenueChart.data.labels = chartData.labels;
        revenueChart.data.datasets[0].data = chartData.data;
        revenueChart.update();
      }

      updateLastRefreshTime();

    })
    .catch(error => {
      console.error("Revenue chart error:", error);
    });
}

// Initial load
loadRevenueChart();

// Refresh every 3 seconds
setInterval(loadRevenueChart, 3000);

function updateLastRefreshTime() {
  const el = document.getElementById("revenue-last-update");
  const now = new Date();

  const time = now.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });

  el.textContent = "updated at " + time;
}

// FIN

// Dépenses quotidiennes (line chart)
let expensesChart = null;

function loadExpensesChart() {
  fetch("/admin/expenses")
    .then(response => response.json())
    .then(chartData => {
      const ctxExpenses = document.getElementById("chart-expenses");
      if (!ctxExpenses) {
        console.error("Canvas #chart-expenses not found");
        return;
      }

      const ctx = ctxExpenses.getContext("2d");

      if (!expensesChart) {
        expensesChart = new Chart(ctx, {
          type: "line",
          data: {
            labels: chartData.labels,
            datasets: [{
              label: "Expenses",
              borderColor: "#000",
              backgroundColor: "transparent",
              data: chartData.data,
              tension: 0.3,
              pointRadius: 3
            }]
          },
          options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true, ticks: { color: "#737373" } },
              x: { ticks: { color: "#737373" } }
            }
          }
        });
      } else {
        expensesChart.data.labels = chartData.labels;
        expensesChart.data.datasets[0].data = chartData.data;
        expensesChart.update();
      }

      updateExpensesLastRefresh();
    })
    .catch(error => {
      console.error("Expenses chart error:", error);
    });
}

// Initial load
loadExpensesChart();

// Refresh every 3 seconds
setInterval(loadExpensesChart, 3000);

function updateExpensesLastRefresh() {
  const el = document.getElementById("expenses-last-update");
  if (!el) return;

  const now = new Date();
  const time = now.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });

  el.textContent = "updated at " + time;
}

// FIN

// Inventaire (line chart)
let inventoryChart = null;

function loadInventoryChart() {
  fetch("/admin/inventory")
    .then(response => response.json())
    .then(chartData => {

      const ctxInventory = document
        .getElementById("chart-inventory")
        .getContext("2d");

      if (!inventoryChart) {
        inventoryChart = new Chart(ctxInventory, {
          type: "line",
          data: {
            labels: chartData.labels,
            datasets: [{
              label: "Stock (units)",
              borderColor: "#000",
              backgroundColor: "transparent",
              data: chartData.data,
              tension: 0.3,
              pointRadius: 3
            }]
          },
          options: {
            responsive: true,
            plugins: {
              legend: { display: false }
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: { color: "#737373" }
              },
              x: {
                ticks: { color: "#737373" }
              }
            }
          }
        });
      } else {
        inventoryChart.data.labels = chartData.labels;
        inventoryChart.data.datasets[0].data = chartData.data;
        inventoryChart.update();
      }

      updateInventoryLastRefresh();

    })
    .catch(error => {
      console.error("Inventory chart error:", error);
    });
}

loadInventoryChart();
setInterval(loadInventoryChart, 3000);

function updateInventoryLastRefresh() {
  const el = document.getElementById("inventory-last-update");
  const now = new Date();

  el.textContent = "updated at " + now.toLocaleTimeString();
}


// FIN

// POUR L'ADMINISTRATEUR SEIGNEUR DES SERVEURS, IL VOIT UN DASHBOARD AVEC DES CHARTS QUI SE METTENT A JOUR TOUT SEULS

// Companies by Sector (pie chart)
let companyChart = null;
function loadCompanyChart() {
  fetch("/manager/companies_by_sector")
    .then(res => res.json())
    .then(chartData => {
      const ctx = document.getElementById("chart-company").getContext("2d");
      if (!companyChart) {
        companyChart = new Chart(ctx, {
          type: "bar",
          data: {
            labels: chartData.labels,
            datasets: [{
              data: chartData.data,
              label: "Companies",
              backgroundColor: ["#000"]
            }]
          }
        });
      } else {
        companyChart.data.labels = chartData.labels;
        companyChart.data.datasets[0].data = chartData.data;
        companyChart.update();
      }
    });
}
loadCompanyChart();
setInterval(loadCompanyChart, 3000);


// Active vs Inactive Subscriptions (doughnut chart)
let activeChart = null;
function loadActiveChart() {
  fetch("/manager/subscriptions_status")
    .then(res => res.json())
    .then(chartData => {
      const ctx = document.getElementById("chart-active").getContext("2d");
      if (!activeChart) {
        activeChart = new Chart(ctx, {
          type: "bar",
          data: {
            labels: chartData.labels,
            datasets: [{
              data: chartData.data,
              label: "Subscriptions",
              backgroundColor: ["#28a745", "#dc3545"]
            }]
          }
        });
      } else {
        activeChart.data.labels = chartData.labels;
        activeChart.data.datasets[0].data = chartData.data;
        activeChart.update();
      }
    });
}
loadActiveChart();
setInterval(loadActiveChart, 3000);


// Upcoming Renewals (bar chart)
let renewalsChart = null;
function loadRenewalsChart() {
  fetch("/manager/upcoming_renewals")
    .then(res => res.json())
    .then(chartData => {
      const ctx = document.getElementById("chart-renewals").getContext("2d");
      if (!renewalsChart) {
        renewalsChart = new Chart(ctx, {
          type: "bar",
          data: {
            labels: chartData.labels,
            datasets: [{
              label: "Renewals",
              data: chartData.data,
              backgroundColor: "#ffc107"
            }]
          }
        });
      } else {
        renewalsChart.data.labels = chartData.labels;
        renewalsChart.data.datasets[0].data = chartData.data;
        renewalsChart.update();
      }
    });
}
loadRenewalsChart();
setInterval(loadRenewalsChart, 3000);

// POUR LE FORMULAIRE DE CREATION D'ABONNEMENT 
document.addEventListener("DOMContentLoaded", function () {
  const categoryDefaults = {
    "Starter": {
      allowed_legal_structures: "individual, ets",
      allowed_industries: "general",
      min_business_size: "personal",
      max_business_size: "small",
      description: "Starter plan for small structures or entrepreneurs."
    },
    "Growth": {
      allowed_legal_structures: "sarl",
      allowed_industries: "tech, retail, services",
      min_business_size: "small",
      max_business_size: "medium",
      description: "Growth plan for SMEs in expansion."
    },
    "Enterprise": {
      allowed_legal_structures: "sa",
      allowed_industries: "industrial, finance",
      min_business_size: "medium",
      max_business_size: "large",
      description: "Enterprise plan for large companies."
    },
    "Corporate": {
      allowed_legal_structures: "sa, holding",
      allowed_industries: "corporate, finance, ngo",
      min_business_size: "large",
      max_business_size: "large",
      description: "Corporate plan for SA or holdings."
    }
  };

  const categorySelect = document.querySelector("select[name='category']");
  categorySelect.addEventListener("change", function () {
    const selected = categorySelect.value;
    const defaults = categoryDefaults[selected];

    if (defaults) {
      document.querySelector("input[name='allowed_legal_structures']").value = defaults.allowed_legal_structures;
      document.querySelector("input[name='allowed_industries']").value = defaults.allowed_industries;
      document.querySelector("select[name='min_business_size']").value = defaults.min_business_size;
      document.querySelector("select[name='max_business_size']").value = defaults.max_business_size;
      document.querySelector("textarea[name='description']").value = defaults.description;
    }
  });
});

