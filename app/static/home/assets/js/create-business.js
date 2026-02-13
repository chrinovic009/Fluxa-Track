document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("business-form");

  const productsSection = document.getElementById("products-section");
  const revenueSection = document.getElementById("revenue-section");
  const expensesSection = document.getElementById("expenses-section");
  const liabilitiesSection = document.getElementById("liabilities-section");

  // Avant l'envoi, ajoute la date
  form.addEventListener("submit", () => {
    document.getElementById("created_at").value = new Date().toISOString();
    // Pas de preventDefault → le formulaire part en POST vers /business
  });

  // Ajouter produit
  document.getElementById("add-product").addEventListener("click", () => {
    const row = document.createElement("div");
    row.className = "dynamic-row";

    row.innerHTML = `
      <input type="text" name="product_name[]" placeholder="Product name">
      <input type="number" name="product_price[]" placeholder="Unit Price" min="0">
      <input type="number" name="product_quantity[]" placeholder="Initial Stock Quantity" min="0">
      <select name="product_category[]">
        <option value="">Category</option>
        <option value="Food">Food</option>
        <option value="Electronics">Electronics</option>
        <option value="Clothing">Clothing</option>
        <option value="Cosmetics">Cosmetics</option>
      </select>
    `;

    productsSection.insertBefore(row, document.getElementById("add-product"));
  });

  // Ajouter revenu
  document.getElementById("add-revenue").addEventListener("click", () => {
    const row = document.createElement("div");
    row.className = "dynamic-row";

    row.innerHTML = `
      <input type="text" name="revenue_source[]" placeholder="Source name">
      <input type="number" name="revenue_amount[]" placeholder="Estimated Amount" min="0">
    `;

    revenueSection.insertBefore(row, document.getElementById("add-revenue"));
  });

  // Ajouter dépense
  document.getElementById("add-expense").addEventListener("click", () => {
    const row = document.createElement("div");
    row.className = "dynamic-row";

    row.innerHTML = `
      <input type="text" name="expense_name[]" placeholder="Expense name">
      <input type="number" name="expense_cost[]" placeholder="Estimated Cost" min="0">
    `;

    expensesSection.insertBefore(row, document.getElementById("add-expense"));
  });

  // Ajouter passif (liability)
  document.getElementById("add-liability").addEventListener("click", () => {
    const row = document.createElement("div");
    row.className = "dynamic-row";

    row.innerHTML = `
      <input type="text" name="liability_name[]" placeholder="Liability name (e.g. Bank Loan)">
      <input type="number" name="liability_value[]" placeholder="Amount" min="0">
      <select name="liability_type[]">
        <option value="">Select Type</option>
        <option value="debt">Debt (Supplier)</option>
        <option value="loan">Loan (Bank)</option>
        <option value="other">Other</option>
      </select>
    `;

    liabilitiesSection.insertBefore(row, document.getElementById("add-liability"));
  });
});
