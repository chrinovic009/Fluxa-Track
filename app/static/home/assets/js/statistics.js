// statistique d'entreprise et de total de transaction
async function updateStats() {
    try {
        const response = await fetch('/stats');
        const data = await response.json();

        document.getElementById('total-companies').textContent = data.total_companies;
        document.getElementById('total-finance').textContent = data.total_finance.toLocaleString();
    } catch (err) {
        console.error('Erreur en récupérant les stats:', err);
    }
}

// Actualise toutes les 2 secondes
setInterval(updateStats, 2000);

// Optionnel: update immédiatement au chargement
updateStats();

// statistique de cartes globale d'administrateur
async function updateDashboard() {
    try {
        const res = await fetch('/admin/dashboard_data_json');
        const data = await res.json();

        document.getElementById('revenue-total').textContent = data.revenue.total.toFixed(2);
        document.getElementById('revenue-growth').textContent = data.revenue.growth_percent + '%';
        document.getElementById('expense-total').textContent = data.expense.total.toFixed(2);
        document.getElementById('profit-net').textContent = data.profit.net.toFixed(2);
        document.getElementById('stock-total').textContent = data.inventory.total_units.toFixed(0) + ' units';
        document.getElementById('low-stock-products').textContent = data.inventory.low_stock_products;
    } catch (err) {
        console.error('Erreur lors de la récupération du dashboard:', err);
    }
}

setInterval(updateDashboard, 2000);
updateDashboard(); // lancement immédiat

// statistique de cartes globale du manager
async function updateAdminDashboard() {
    try {
        const res = await fetch('/manager/admin_dashboard_json');
        const data = await res.json();

        document.getElementById('total-companies').textContent = data.total_companies;
        document.getElementById('active-subscriptions').textContent = data.active_subscriptions;
        document.getElementById('inactive-subscriptions').textContent = data.inactive_subscriptions;
        document.getElementById('total-budget').textContent = data.total_budget.toFixed(2) + ' $';
    } catch (err) {
        console.error('Erreur lors de la récupération du dashboard admin:', err);
    }
}

setInterval(updateAdminDashboard, 2000);
updateAdminDashboard(); // lancement immédiat


