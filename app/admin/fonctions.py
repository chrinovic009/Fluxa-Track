from datetime import datetime, timedelta, date
from sqlalchemy import func, case
from decimal import Decimal
from app.utils.authentication.models import (
    RevenueSource, Expense, InventoryMovement, Product, 
    CompanyUser, AuditLog, User, Asset, Liability, ReportSnapshot
    )
from app import db

def get_admin_dashboard_metrics(company_id):
    today = datetime.utcnow()
    start_of_week = today - timedelta(days=7)
    start_of_last_week = today - timedelta(days=14)

    # --- REVENUE ---
    total_revenue = db.session.query(
        func.coalesce(func.sum(RevenueSource.amount), 0)
    ).filter(
        RevenueSource.company_id == company_id
    ).scalar()

    last_week_revenue = db.session.query(
        func.coalesce(func.sum(RevenueSource.amount), 0)
    ).filter(
        RevenueSource.company_id == company_id,
        RevenueSource.created_at >= start_of_week
    ).scalar()

    previous_week_revenue = db.session.query(
        func.coalesce(func.sum(RevenueSource.amount), 0)
    ).filter(
        RevenueSource.company_id == company_id,
        RevenueSource.created_at.between(start_of_last_week, start_of_week)
    ).scalar()

    revenue_growth = calculate_growth(last_week_revenue, previous_week_revenue)

    # --- EXPENSES ---
    total_expense = db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.company_id == company_id
    ).scalar()

    # --- NET PROFIT ---
    net_profit = total_revenue - total_expense

    # --- INVENTORY ---
    stock_quantity = db.session.query(
        func.coalesce(func.sum(
            InventoryMovement.quantity *
            case(
                (InventoryMovement.movement_type.in_(["out", "sale"]), -1),
                else_=1
            )
        ), 0)
    ).filter(
        InventoryMovement.company_id == company_id
    ).scalar()

    low_stock_products = db.session.query(Product).join(
        InventoryMovement
    ).group_by(Product.id).having(
        func.sum(InventoryMovement.quantity) < 10
    ).count()

    return {
        "revenue": {
            "total": float(total_revenue),
            "growth_percent": revenue_growth
        },
        "expense": {
            "total": float(total_expense)
        },
        "profit": {
            "net": float(net_profit)
        },
        "inventory": {
            "total_units": int(stock_quantity),
            "low_stock_products": low_stock_products
        }
    }

def calculate_growth(current, previous):
    if previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100, 2)


# pour le graphique de revenues
def get_revenue_by_source(company_id):
    results = (
        db.session.query(
            RevenueSource.name.label("source"),
            func.sum(RevenueSource.amount).label("total")
        )
        .filter(RevenueSource.company_id == company_id)
        .group_by(RevenueSource.name)
        .all()
    )

    return {
        "labels": [row.source for row in results],
        "data": [float(row.total) for row in results]
    }

# pour le graphique de depenses
def get_daily_expenses(company_id, days=7):
    start_date = date.today() - timedelta(days=days - 1)

    results = (
        db.session.query(
            func.date(Expense.created_at).label("day"),
            func.sum(Expense.amount).label("total")
        )
        .filter(
            Expense.company_id == company_id,
            Expense.created_at >= start_date
        )
        .group_by(func.date(Expense.created_at))
        .order_by(func.date(Expense.created_at))
        .all()
    )

    labels = []
    data = []

    for row in results:
        # row.day est une chaîne "YYYY-MM-DD"
        day_obj = datetime.strptime(row.day, "%Y-%m-%d").date()
        labels.append(day_obj.strftime("%a"))  # Mon, Tue, Wed...
        data.append(float(row.total))

    return {
        "labels": labels,
        "data": data
    }

# pour l'inventaire
def get_inventory_status(company_id):
    results = (
        db.session.query(
            Product.name.label("product"),
            func.sum(
                case(
                    (
                        InventoryMovement.movement_type.in_(["out", "sale"]),
                        -InventoryMovement.quantity
                    ),
                    else_=InventoryMovement.quantity
                )
            ).label("stock")
        )
        .join(InventoryMovement, InventoryMovement.product_id == Product.id)
        .filter(Product.company_id == company_id)
        .group_by(Product.name)
        .order_by(Product.name)
        .all()
    )

    return {
        "labels": [row.product for row in results],
        "data": [int(row.stock or 0) for row in results]
    }

# pour le bilan et la trésorerie
def get_balance_sheet(company_id):
    # Actifs
    total_assets = db.session.query(func.sum(Asset.value))\
        .filter(Asset.company_id == company_id).scalar() or 0

    # Passifs
    total_liabilities = db.session.query(func.sum(Liability.value))\
        .filter(Liability.company_id == company_id).scalar() or 0

    # Capitaux propres
    equity = total_assets - total_liabilities

    return {
        "total_assets": float(total_assets),
        "total_liabilities": float(total_liabilities),
        "equity": float(equity),
        "formula_check": float(total_assets) == float(total_liabilities + equity)
    }

def get_monthly_report(company_id):
    # Période courante (mois en cours)
    today = date.today()
    start = datetime(today.year, today.month, 1)  # utiliser datetime pour comparer avec created_at

    # Total revenus
    total_revenue = db.session.query(func.sum(RevenueSource.amount))\
        .filter(RevenueSource.company_id == company_id,
                RevenueSource.created_at >= start).scalar() or 0

    # Total dépenses
    total_expense = db.session.query(func.sum(Expense.amount))\
        .filter(Expense.company_id == company_id,
                Expense.created_at >= start).scalar() or 0

    # Résultat net
    net_result = total_revenue - total_expense

    return {
        "total_revenue": float(total_revenue),
        "total_expense": float(total_expense),
        "net_result": float(net_result)
    }

def get_cash_flow(company_id):
    # Revenus sources
    total_revenue = db.session.query(func.sum(RevenueSource.amount))\
        .filter(RevenueSource.company_id == company_id).scalar() or 0

    # Dépenses
    total_expense = db.session.query(func.sum(Expense.amount))\
        .filter(Expense.company_id == company_id).scalar() or 0

    # Ventes (inclure InventoryMovement)
    sales = db.session.query(
        func.sum(Product.unit_price * InventoryMovement.quantity)
    ).select_from(InventoryMovement) \
     .join(Product, Product.id == InventoryMovement.product_id) \
     .filter(
         InventoryMovement.company_id == company_id,
         InventoryMovement.movement_type == "sale"
     ).scalar() or 0

    cash_flow = (total_revenue + sales) - total_expense
    return float(cash_flow)

# pour le bilan et la trésorerie par point de vente
def get_balance_sheet_for_sale_point(company_id, sale_point):
    # Actifs par point de vente
    total_assets = db.session.query(func.sum(Asset.value))\
        .join(CompanyUser, Asset.company_id == CompanyUser.company_id)\
        .filter(
            Asset.company_id == company_id,
            CompanyUser.sale_point == sale_point
        ).scalar() or 0

    # Passifs par point de vente
    total_liabilities = db.session.query(func.sum(Liability.value))\
        .join(CompanyUser, Liability.company_id == CompanyUser.company_id)\
        .filter(
            Liability.company_id == company_id,
            CompanyUser.sale_point == sale_point
        ).scalar() or 0

    # Capitaux propres
    equity = total_assets - total_liabilities

    return {
        "total_assets": float(total_assets),
        "total_liabilities": float(total_liabilities),
        "equity": float(equity),
        "formula_check": float(total_assets) == float(total_liabilities + equity)
    }

def get_cash_flow_for_admin(company_id, sale_point):
    # Revenus sources par point de vente
    total_revenue = db.session.query(func.sum(RevenueSource.amount))\
        .join(CompanyUser, RevenueSource.company_user_id == CompanyUser.id)\
        .filter(
            RevenueSource.company_id == company_id,
            CompanyUser.sale_point == sale_point
        ).scalar() or 0

    # Dépenses par point de vente
    total_expense = db.session.query(func.sum(Expense.amount))\
        .join(CompanyUser, Expense.company_user_id == CompanyUser.id)\
        .filter(
            Expense.company_id == company_id,
            CompanyUser.sale_point == sale_point
        ).scalar() or 0

    # Ventes par point de vente
    sales = db.session.query(
    func.sum(Product.unit_price * InventoryMovement.quantity)
        ).select_from(InventoryMovement) \
        .join(Product, Product.id == InventoryMovement.product_id) \
        .join(CompanyUser, InventoryMovement.company_user_id == CompanyUser.id) \
        .filter(
            InventoryMovement.company_id == company_id,
            CompanyUser.sale_point == sale_point,   # <--- filtrage par point de vente
            InventoryMovement.movement_type == "sale"
        ).scalar() or 0

    cash_flow = (total_revenue + sales) - total_expense
    return float(cash_flow)

# moyenne des ventes quotidiennes par administrateur
def get_admin_daily_average(admin_id, company_id):
    today = date.today()
    start = datetime(today.year, today.month, 1)

    # Somme des ventes faites par cet admin
    total_sales = db.session.query(
        func.sum(Product.unit_price * InventoryMovement.quantity)
    ).select_from(InventoryMovement) \
     .join(Product, Product.id == InventoryMovement.product_id) \
     .filter(
         InventoryMovement.company_id == company_id,
         InventoryMovement.actor_id == admin_id,
         InventoryMovement.movement_type == "sale",
         InventoryMovement.created_at >= start
     ).scalar() or 0

    # Nombre de jours écoulés dans le mois
    days_passed = (today - start.date()).days + 1
    daily_average = total_sales / days_passed if days_passed > 0 else 0

    return float(daily_average)

# pour afficher le total d'un produit en stock
def get_product_stock(product_id, company_id):
    movements = InventoryMovement.query.filter_by(
        product_id=product_id,
        company_id=company_id
    ).all()

    stock = 0
    for m in movements:
        if m.movement_type in ("initial", "in"):
            stock += m.quantity
        elif m.movement_type in ("out", "sale"):
            stock -= m.quantity
        elif m.movement_type == "adjustment":
            stock += m.quantity  # quantité peut être positive ou négative

    # Empêcher stock négatif
    if stock < 0:
        stock = 0

    return stock

# detection du nombre de point de vente
def get_sale_points(company_id):
    return CompanyUser.query.filter_by(
        company_id=company_id
    ).all()

# calcul des revenues par point de vente
def get_revenue_by_sale_point(company_id):
    sale_points = get_sale_points(company_id)

    # S'il n'y a qu'un seul point de vente, on garde l'ancien comportement
    if len(sale_points) <= 1:
        return get_revenue_by_source(company_id)

    results = (
        db.session.query(
            CompanyUser.sale_point.label("sale_point"),
            func.sum(RevenueSource.amount).label("total")
        )
        .join(CompanyUser, CompanyUser.id == RevenueSource.company_user_id)
        .filter(RevenueSource.company_id == company_id)
        .group_by(CompanyUser.sale_point)
        .order_by(CompanyUser.sale_point)
        .all()
    )

    return {
        "labels": [row.sale_point for row in results],
        "data": [float(row.total) for row in results]
    }

# calcul des depenses par point de vente
def get_expenses_by_sale_point(company_id):
    sale_points = get_sale_points(company_id)

    if len(sale_points) <= 1:
        return get_daily_expenses(company_id)

    results = (
        db.session.query(
            CompanyUser.sale_point.label("sale_point"),
            func.sum(Expense.amount).label("total")
        )
        .join(CompanyUser, CompanyUser.id == Expense.company_user_id)
        .filter(Expense.company_id == company_id)
        .group_by(CompanyUser.sale_point)
        .order_by(CompanyUser.sale_point)
        .all()
    )

    return {
        "labels": [row.sale_point for row in results],
        "data": [float(row.total) for row in results]
    }

# calcul de l'inventaire par point de vente
def get_inventory_by_sale_point(company_id):
    sale_points = get_sale_points(company_id)

    if len(sale_points) <= 1:
        return get_inventory_status(company_id)

    results = (
        db.session.query(
            CompanyUser.sale_point.label("sale_point"),
            func.sum(
                case(
                    (InventoryMovement.movement_type.in_(["out", "sale"]), -InventoryMovement.quantity),
                    else_=InventoryMovement.quantity
                )
            ).label("stock")
        )
        .join(CompanyUser, CompanyUser.id == InventoryMovement.company_user_id)
        .filter(InventoryMovement.company_id == company_id)
        .group_by(CompanyUser.sale_point)
        .order_by(CompanyUser.sale_point)
        .all()
    )

    return {
        "labels": [row.sale_point for row in results],
        "data": [int(row.stock or 0) for row in results]
    }

# rapport de revenue pour les points de vente:
def get_revenue_report(company_id):
    rows = []

    revenues = (
        db.session.query(
            RevenueSource,
            CompanyUser,
            User
        )
        .join(CompanyUser, RevenueSource.company_user_id == CompanyUser.id)
        .join(User, CompanyUser.user_id == User.id)
        .filter(RevenueSource.company_id == company_id)
        .all()
    )

    total = 0

    for rev, cu, user in revenues:
        rows.append({
            "store": cu.sale_point,
            "unit": cu.role,
            "manager": f"{user.name} {user.family_name}",
            "source": rev.name,
            "payment": "N/A",
            "amount": float(rev.amount),
            "currency": cu.company.currency,
            "date": rev.created_at.strftime("%Y-%m-%d"),
            "status": "Confirmed",
            "notes": ""
        })
        total += float(rev.amount)

    return {"rows": rows, "total": total}

# rapport de depenses pour les points de vente:
def get_expense_report(company_id):
    rows = []
    total = 0

    expenses = (
        db.session.query(Expense, CompanyUser, User)
        .join(CompanyUser, Expense.company_user_id == CompanyUser.id)
        .join(User, CompanyUser.user_id == User.id)
        .filter(Expense.company_id == company_id)
        .all()
    )

    for exp, cu, user in expenses:
        rows.append({
            "store": cu.sale_point,
            "category": "General",
            "description": exp.name,
            "responsible": user.name,
            "payment": "Cash",
            "cost": float(exp.amount),
            "currency": cu.company.currency,
            "date": exp.created_at.strftime("%Y-%m-%d"),
            "status": "Approved",
            "remarks": ""
        })
        total += float(exp.amount)

    return {"rows": rows, "total": total}

# rapport d'inventaire pour les points de vente:
def get_inventory_report(company_id):
    rows = []

    products = Product.query.filter_by(company_id=company_id).all()

    for product in products:
        stock = (
            db.session.query(
                func.sum(
                    case(
                        (InventoryMovement.movement_type.in_(["out", "sale"]), -InventoryMovement.quantity),
                        else_=InventoryMovement.quantity
                    )
                )
            )
            .filter(
                InventoryMovement.product_id == product.id,
                InventoryMovement.company_id == company_id
            )
            .scalar() or 0
        )

        value = stock * float(product.unit_price)

        rows.append({
            "store": product.company_user.sale_point,
            "product": product.name,
            "category": product.category,
            "stock": stock,
            "min": 0,
            "price": float(product.unit_price),
            "value": value,
            "supplier": "-",
            "status": "Critical" if stock < 5 else "OK",
            "updated": product.created_at.strftime("%Y-%m-%d")
        })

    total = sum(r["value"] for r in rows)
    return {"rows": rows, "total": total}

# rapport pour le cashflow de tous les points de vente:
def get_cashflow_report(company_id):
    results = (
        db.session.query(
            CompanyUser.sale_point.label("store"),

            func.coalesce(func.sum(RevenueSource.amount), 0).label("revenue"),
            func.coalesce(func.sum(Expense.amount), 0).label("expense"),

            func.coalesce(
                func.sum(
                    case(
                        (InventoryMovement.movement_type == "sale",
                         InventoryMovement.quantity * Product.unit_price),
                        else_=0
                    )
                ), 0
            ).label("sales")
        )
        .select_from(CompanyUser)
        .outerjoin(RevenueSource, RevenueSource.company_user_id == CompanyUser.id)
        .outerjoin(Expense, Expense.company_user_id == CompanyUser.id)
        .outerjoin(InventoryMovement, InventoryMovement.company_user_id == CompanyUser.id)
        .outerjoin(Product, Product.id == InventoryMovement.product_id)
        .filter(CompanyUser.company_id == company_id)
        .group_by(CompanyUser.sale_point)
        .order_by(CompanyUser.sale_point)
        .all()
    )

    rows = []
    total_cashflow = 0

    for row in results:
        cashflow = (row.revenue + row.sales) - row.expense
        total_cashflow += cashflow

        rows.append({
            "store": row.store,
            "type": "Net Cash Flow",
            "source": "Operations",
            "amount": float(cashflow),
            "currency": "USD",
            "impact": "Positive" if cashflow >= 0 else "Negative",
            "date": date.today().isoformat(),
            "recorded": "System",
            "status": "Confirmed",
            "notes": "Computed from revenues, sales and expenses"
        })

    return {
        "rows": rows,
        "total": float(total_cashflow)
    }

# pour generer un snapshot
def generate_report_snapshot(company_id, company_user_id):

    today = date.today()

    # 🔹 Total revenue = ventes + sources revenus
    sales_total = db.session.query(
        func.sum(InventoryMovement.quantity * Product.unit_price)
    ).join(Product).filter(
        InventoryMovement.company_id == company_id,
        InventoryMovement.movement_type == "sale"
    ).scalar() or 0

    other_revenue = db.session.query(
        func.sum(RevenueSource.amount)
    ).filter(
        RevenueSource.company_id == company_id
    ).scalar() or 0

    total_revenue = sales_total + other_revenue

    # 🔹 Total expense
    total_expense = db.session.query(
        func.sum(Expense.amount)
    ).filter(
        Expense.company_id == company_id
    ).scalar() or 0

    net_result = total_revenue - total_expense

    snapshot = ReportSnapshot(
        company_id=company_id,
        company_user_id=company_user_id,
        period_start=today,
        period_end=today,
        total_revenue=total_revenue,
        total_expense=total_expense,
        net_result=net_result
    )

    db.session.add(snapshot)
    db.session.commit()
