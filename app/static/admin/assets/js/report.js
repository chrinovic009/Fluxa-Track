// ================= REPORT DEFINITIONS =================
const reports = {

  revenue: {
    title: "Revenue & Income",
    columns: [
      { label: "Sales Point", key: "store" },
      { label: "Business Unit", key: "unit" },
      { label: "Manager", key: "manager" },
      { label: "Source", key: "source" },
      { label: "Payment Method", key: "payment" },
      { label: "Gross Amount", key: "amount" },
      { label: "Currency", key: "currency" },
      { label: "Transaction Date", key: "date" },
      { label: "Status", key: "status" },
      { label: "Notes", key: "notes" }
    ]
  },

  expenses: {
    title: "Expenses",
    columns: [
      { label: "Sales Point", key: "store" },
      { label: "Category", key: "category" },
      { label: "Description", key: "description" },
      { label: "Responsible", key: "responsible" },
      { label: "Payment Method", key: "payment" },
      { label: "Cost", key: "cost" },
      { label: "Currency", key: "currency" },
      { label: "Expense Date", key: "date" },
      { label: "Approval Status", key: "status" },
      { label: "Remarks", key: "remarks" }
    ]
  },

  cashflow: {
    title: "Cash Flow",
    columns: [
      { label: "Sales Point", key: "store" },
      { label: "Flow Type", key: "type" },
      { label: "Source / Reason", key: "source" },
      { label: "Amount", key: "amount" },
      { label: "Currency", key: "currency" },
      { label: "Impact", key: "impact" },
      { label: "Transaction Date", key: "date" },
      { label: "Recorded By", key: "recorded" },
      { label: "Status", key: "status" },
      { label: "Notes", key: "notes" }
    ]
  },

  inventory: {
    title: "Inventory",
    columns: [
      { label: "Sales Point", key: "store" },
      { label: "Product Name", key: "product" },
      { label: "Category", key: "category" },
      { label: "Current Stock", key: "stock" },
      { label: "Minimum Stock", key: "min" },
      { label: "Unit Price", key: "price" },
      { label: "Stock Value", key: "value" },
      { label: "Supplier", key: "supplier" },
      { label: "Status", key: "status" },
      { label: "Last Updated", key: "updated" }
    ]
  }
};

// ================= DOM =================
const buttons = document.querySelectorAll(".report-btn");
const tableHead = document.getElementById("table-head");
const tableBody = document.getElementById("table-body");
const tableTotal = document.getElementById("table-total");
const reportTitle = document.getElementById("report-title");

// ================= EVENTS =================
buttons.forEach(btn => {
  btn.addEventListener("click", () => {
    buttons.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    loadReport(btn.dataset.report);
  });
});

// ================= DEFAULT LOAD =================
document.addEventListener("DOMContentLoaded", () => {
  const defaultBtn = document.querySelector('[data-report="revenue"]');
  defaultBtn.classList.add("active");
  loadReport("revenue");
});

// ================= CORE =================
async function loadReport(type) {
  const report = reports[type];
  if (!report) return;

  reportTitle.textContent = `${report.title} (All Sales Points)`;
  tableHead.innerHTML = "";
  tableBody.innerHTML = "";
  tableTotal.textContent = "...";

  try {
    const response = await fetch(`/admin/api/reports?type=${type}`);
    if (!response.ok) throw new Error("Failed to fetch report data");

    const data = await response.json();

    // Build table header
    report.columns.forEach(col => {
      const th = document.createElement("th");
      th.textContent = col.label;
      th.className =
        "text-uppercase text-secondary text-xxs font-weight-bolder opacity-7";
      tableHead.appendChild(th);
    });

    let total = 0;

    // Build rows
    data.rows.forEach(row => {
      const tr = document.createElement("tr");

      report.columns.forEach(col => {
        const td = document.createElement("td");
        const value = row[col.key] ?? "-";
        td.textContent = value;
        td.className = "text-sm";
        tr.appendChild(td);

        if (typeof value === "number") {
          total += value;
        }
      });

      tableBody.appendChild(tr);
    });

    tableTotal.textContent =
      data.total !== undefined
        ? data.total.toLocaleString()
        : total.toLocaleString();

  } catch (error) {
    console.error(error);
    tableBody.innerHTML = `
      <tr>
        <td colspan="10" class="text-center text-danger">
          Failed to load report data
        </td>
      </tr>
    `;
    tableTotal.textContent = "-";
  }
}
