from sympy import product, use
import secrets
import string
from werkzeug.security import generate_password_hash
from app.utils.admin import blueprint
from app import db, UPLOAD_FOLDER, csrf, socketio, bcrypt
from flask import render_template, flash, redirect, url_for, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func
from decimal import Decimal
from app.utils.decorator.company import company_required, admin_required
from app.manager.fonctions import subscription_required
from app.utils.prediction.service.sales_prediction import predict_sales

from app.admin.fonctions import (
                                    generate_report_snapshot, get_admin_dashboard_metrics, get_monthly_report, get_cash_flow,
                                    get_admin_daily_average, get_product_stock,get_balance_sheet_for_sale_point,
                                    get_cash_flow_for_admin, get_revenue_by_sale_point, get_expenses_by_sale_point,
                                    get_inventory_by_sale_point, get_revenue_report, get_expense_report, get_inventory_report,
                                    get_cashflow_report, get_balance_sheet
                                )

from flask_login import login_required, current_user
from app.utils.authentication.models import (
                                            User, Company, Notifications,
                                            CompanyUser, Product, InventoryMovement, RevenueSource, 
                                            Expense, TemporaryCredential, AuditLog, Asset, Liability,
                                            SubscriptionPlan, CompanySubscription
                                            )

# pour la page d'acceuil du tableau de bord admin
@blueprint.route('/admin', methods=['POST', 'GET'])
@login_required
@company_required
@admin_required
@subscription_required
def admin():

    user = User.query.filter_by(id=current_user.id).first()
    company_link = CompanyUser.query.filter_by(user_id=user.id).first()

    company_subscription = CompanySubscription.query.filter_by(
        company_id=company_link.company_id,
        status="active"
    ).first()

    subscription_plan = company_subscription.plan if company_subscription else None


    dashboard_data = get_admin_dashboard_metrics(company_link.company_id)

    # Revenus
    revenues = RevenueSource.query.filter_by(company_id=company_link.company_id).all()

    # Dépenses
    expenses = Expense.query.filter_by(company_id=company_link.company_id).all()

    # Construire une liste mixte pour le tableau
    finance_rows = []

    for r in revenues:
        finance_rows.append({
            "type": "Income",
            "source": r.name,
            "amount": float(r.amount),
            "currency": company_link.company.currency,
            "status": "Confirmed"  # ou autre logique
        })

    for e in expenses:
        finance_rows.append({
            "type": "Expense",
            "source": e.name,
            "amount": float(e.amount),
            "currency": company_link.company.currency,
            "status": "Approved"  # ou autre logique
        })

    # Tous les points de vente de l’entreprise 
    company_users = CompanyUser.query.filter_by(company_id=company_link.company_id).all()

    # Récupérer les prédictions par point de vente 
    predictions = [] 
    for cu in company_users: 
        products = Product.query.filter_by(company_id=company_link.company_id, company_user_id=cu.id).all() 
        
        for product in products: 
            prediction = predict_sales(company_link.company_id, product.id, cu.sale_point, cu.id) 
            predictions.append(prediction)

    return render_template(
                        'admin/dashboard.html', page_active="admin", 
                        dashboard_data=dashboard_data, user=user, company_link=company_link,
                        finance_rows=finance_rows, predictions=predictions, subscription_plan=subscription_plan
                        )

# pour le graphique de sources de revenus
@blueprint.route("/revenue")
@login_required
@company_required
@admin_required
@subscription_required
def revenue():
    user = User.query.filter_by(id=current_user.id).first()
    company_link = CompanyUser.query.filter_by(user_id=user.id).first()
    company_id = company_link.company_id

    chart_data = get_revenue_by_sale_point(company_id)

    return {
        "labels": chart_data["labels"],
        "data": chart_data["data"]
    }

# pour le graphique des dépenses
@blueprint.route("/expenses")
@login_required
@company_required
@admin_required
@subscription_required
def expenses():
    company_link = CompanyUser.query.filter_by(user_id=current_user.id).first()
    if not company_link:
        return jsonify({"labels": [], "data": []})

    company_id = company_link.company_id

    chart_data = get_expenses_by_sale_point(company_id)

    return jsonify({
        "labels": chart_data["labels"],
        "data": chart_data["data"]
    })

# pour le graphique de l'inventaire
@blueprint.route("/inventory")
@login_required
@company_required
@admin_required
@subscription_required
def inventory():
    user = User.query.filter_by(id=current_user.id).first()
    company_link = CompanyUser.query.filter_by(user_id=user.id).first()
    company_id = company_link.company_id

    chart_data = get_inventory_by_sale_point(company_id)

    return {
        "labels": chart_data["labels"],
        "data": chart_data["data"]
    }

# pour la page de vente
@blueprint.route('/sales', methods=['POST', 'GET'])
@login_required
@company_required
def sales():
    # Récupérer l'utilisateur connecté
    user = User.query.filter_by(id=current_user.id).first()

    # Lien principal entre user et entreprise
    company_link = CompanyUser.query.filter_by(user_id=user.id).first()
    if not company_link:
        flash("Vous n'êtes lié à aucune entreprise.", "danger")
        return redirect(url_for("home_blueprint.index"))
    
    company_subscription = CompanySubscription.query.filter_by(
        company_id=company_link.company_id,
        status="active"
    ).first()

    subscription_plan = company_subscription.plan if company_subscription else None

    # Tous les points de vente de l'entreprise
    company_users = CompanyUser.query.filter_by(
        company_id=company_link.company_id
    ).all()

    points = CompanyUser.query.filter_by(
        company_id=company_link.company_id
    ).first()

    # Tous les liens user ↔ company (si user est lié à plusieurs entreprises)
    company_links = CompanyUser.query.filter_by(user_id=user.id).all()

    # Rapports globaux
    report = get_monthly_report(company_link.company_id) 
    bilan = get_balance_sheet(company_link.company_id)
    cash_flow = get_cash_flow(company_link.company_id)

    # Rapports par administrateur / point de vente
    report_admin = get_balance_sheet_for_sale_point(company_link.company_id, company_link.sale_point)
    cash_flow_admin = get_cash_flow_for_admin(company_link.company_id, company_link.sale_point)

    # Produits de l'entreprise
    products = Product.query.filter_by(company_id=company_link.company_id).all()

    productss = Product.query.filter_by( company_id=company_link.company_id, company_user_id=company_link.id).all()

    product_statss = [] 
    for product in productss: 
        stock = get_product_stock(product.id, company_link.company_id) 
        product_statss.append({ 
            "id": product.id, 
            "name": product.name, 
            "category": product.category, 
            "unit_price": float(product.unit_price), 
            "stock": stock, 
            "sale_point": 
            company_link.sale_point })

    product_stats = []
    for product in products:
        stock = get_product_stock(product.id, company_link.company_id)
        company_user = CompanyUser.query.get(product.company_user_id)  # récupérer le point de vente du produit
        product_stats.append({
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "unit_price": float(product.unit_price),
            "stock": stock,
            "sale_point": company_user.sale_point if company_user else "N/A"  # ajouter le point de vente
        })

    # Historique des actions de l’agent connecté
    transactions = AuditLog.query.filter_by(
        actor_id=current_user.id,
        company_user_id=company_link.id
    ).order_by(AuditLog.created_at.desc()).all()

    return render_template(
        'admin/sales.html',
        page_active="sales",
        company_link=company_link,
        user=user,
        company_links=company_links,
        report=report,
        cash_flow=cash_flow,
        product_stats=product_stats,
        report_admin=report_admin,
        cash_flow_admin=cash_flow_admin,
        sale_point=company_users,
        product_statss=product_statss,
        transactions=transactions, balance_sheet=bilan, 
        subscription_plan=subscription_plan, points=points
    )

# pour ajouter un produit via modal
@blueprint.route('/add-product', methods=["POST"])
@login_required
@company_required
@admin_required
@subscription_required
@csrf.exempt
def add_product():
    user = User.query.filter_by(id=current_user.id).first()

    company_user_id = request.form.get("company_user_id")
    name = request.form.get("product_name")
    price = request.form.get("product_price")
    category = request.form.get("product_category")
    quantity = request.form.get("product_quantity")

    # Vérifier que l'utilisateur est lié à une entreprise
    company_link = CompanyUser.query.filter_by(user_id=user.id).first()
    company_salePoint = CompanyUser.query.filter_by(id=company_user_id, company_id=company_link.company_id).first()
    if not company_salePoint:
        flash("You are not affiliated with any company.", "danger")
        return redirect(url_for("admin_blueprint.sales"))

    company_id = company_salePoint.company_id

    # Créer le produit
    product = Product(
        company_id=company_id,
        company_user_id=company_salePoint.id,
        name=name,
        category=category,
        unit_price=price,
        created_at=datetime.utcnow()
    )
    db.session.add(product)
    db.session.flush()  # pour générer product.id

    # Créer le mouvement d'inventaire initial
    inventory = InventoryMovement(
        product_id=product.id,
        company_id=company_id,
        company_user_id=company_salePoint.id,
        actor_id=current_user.id,
        movement_type="initial",
        quantity=int(quantity),
        created_at=datetime.utcnow()
    )
    db.session.add(inventory)

    # Enregistrer comme actif (stock)
    asset = Asset(
        company_id=company_id,
        type="stock",
        name=f"Stock initial {name}",
        value=float(price) * int(quantity),
        created_at=datetime.utcnow()
    )
    db.session.add(asset)

    # Créer un historique (AuditLog)
    log = AuditLog(
        company_id=company_id,
        company_user_id=company_salePoint.id,
        actor_id=user.id,
        action_type="Adding Product",                 # type d’action
        entity=f"{product.name}",                     # module concerné
        entity_id=product.id,                 # ID du produit créé
        sale_point=company_salePoint.sale_point,   # point de vente
        impact_value=quantity,                # impact sur le stock
        impact_unit="Units",                  # unité
        status="success",                     # statut
        description=f"Added product '{name}' with initial stock of {quantity}",
        created_at=datetime.utcnow()
    )
    db.session.add(log)

    db.session.commit()
    flash("Product added successfully!", "success")
    return redirect(url_for("admin_blueprint.sales"))

# pour supprimer un produit via modal
@blueprint.route("/delete-product", methods=["POST"])
@login_required
@company_required
@admin_required
@subscription_required
@csrf.exempt
def delete_product():
    product_id = request.form.get("product_id")

    # Récupérer le produit
    product = Product.query.get_or_404(product_id)

    # Vérifier que l'utilisateur est lié à la même entreprise
    company_link = CompanyUser.query.filter_by(user_id=current_user.id).first()
    if not company_link or product.company_id != company_link.company_id:
        flash("You are not allowed to delete this product.", "danger")
        return redirect(url_for("admin_blueprint.sales"))

    # Récupérer le point de vente lié au produit
    company_salePoint = CompanyUser.query.get(product.company_user_id)

    # Récupérer le stock avant suppression
    inventor = InventoryMovement.query.filter_by(product_id=product.id).first()
    stock_value = inventor.quantity if inventor else 0

    # Supprimer tous les mouvements liés
    InventoryMovement.query.filter_by(product_id=product.id).delete()

    # Supprimer l'actif lié au produit
    Asset.query.filter_by(company_id=product.company_id, name=f"Stock initial {product.name}").delete()

    # Supprimer le produit
    db.session.delete(product)

    # Créer un historique (AuditLog)
    log = AuditLog(
        company_id=product.company_id,
        company_user_id=company_salePoint.id,
        actor_id=current_user.id,
        action_type="Delete Product",                 # type d’action
        entity=f"{product.name}",                     # module concerné
        entity_id=product.id,                 # ID du produit supprimé
        sale_point=company_salePoint.sale_point,   # point de vente correct
        impact_value=stock_value,             # stock supprimé
        impact_unit="Units",                  # unité
        status="success",                     # statut
        description=f"Deleted product '{product.name}' with stock of {stock_value}",
        created_at=datetime.utcnow()
    )
    db.session.add(log)

    # Commit final
    db.session.commit()

    flash("Product and all related inventory records deleted successfully.", "success")
    return redirect(url_for("admin_blueprint.sales"))

# pour modifier un produit via modal
@blueprint.route("/edit-product", methods=["POST"])
@login_required
@company_required
@admin_required
@subscription_required
@csrf.exempt
def edit_product():
    product_id = request.form.get("product_id")
    name = request.form.get("name")
    price = request.form.get("price")
    stock_adjustment = int(request.form.get("stock_adjustment", 0))

    product = Product.query.get_or_404(product_id)

    # Mettre à jour les champs du produit
    product.name = name
    product.unit_price = float(price)  # conversion en float

    # Gérer l'ajustement du stock si nécessaire
    if stock_adjustment != 0:
        # Récupérer le CompanyUser lié au produit
        company_salePoint = CompanyUser.query.get(product.company_user_id)
        if not company_salePoint:
            flash("No company linked to this product.", "danger")
            return redirect(url_for("admin_blueprint.sales"))

        # Vérifier le stock actuel
        current_stock = get_product_stock(product.id, product.company_id)

        # Calculer le nouveau stock
        new_stock = current_stock + stock_adjustment

        # Empêcher un stock négatif
        if new_stock < 0:
            flash("Stock cannot be less than 0. Adjustment cancelled.", "danger")
            return redirect(url_for("admin_blueprint.sales"))

        # Créer le mouvement d'inventaire
        inventory_movement = InventoryMovement(
            product_id=product.id,
            company_id=product.company_id,
            company_user_id=company_salePoint.id,   # point de vente correct
            actor_id=current_user.id,
            movement_type="adjustment",
            quantity=stock_adjustment,
            created_at=datetime.utcnow()
        )
        db.session.add(inventory_movement)

        # Mettre à jour l'actif (stock) 
        asset = Asset.query.filter_by(company_id=product.company_id, name=f"Stock initial {product.name}").first() 
        if asset: 
            asset.value = float(product.unit_price) * new_stock 
        else: # Si pas trouvé, créer un nouvel actif 
            asset = Asset( company_id=product.company_id, type="stock", name=f"Stock initial {product.name}", value=float(product.unit_price) * new_stock, created_at=datetime.utcnow() ) 
            db.session.add(asset)

        # Créer un historique (AuditLog)
        log = AuditLog(
            company_id=product.company_id,
            actor_id=current_user.id,
            company_user_id=company_salePoint.id,   # point de vente correct
            action_type="Adjustment",
            entity=f"{product.name}",
            entity_id=product.id,
            sale_point=company_salePoint.sale_point,   # bon point de vente
            impact_value=stock_adjustment,
            impact_unit="Units",
            status="success",
            description=f"Adjusted product '{product.name}' stock by {stock_adjustment}",
            created_at=datetime.utcnow()
        )
        db.session.add(log)

    db.session.commit()
    flash("Product and stock updated successfully.", "success")
    return redirect(url_for("admin_blueprint.sales"))

# pour aouter une depense via modal
@blueprint.route('/add-expense', methods=["POST"])
@login_required
@company_required
@admin_required
@subscription_required
@csrf.exempt
def add_expense():
    name = request.form.get("expense_name")
    cost = request.form.get("expense_cost")
    company_user_id = request.form.get("company_user_id")  # ID du point de vente choisi

    # Vérifier que l'utilisateur est lié à une entreprise
    company_link = CompanyUser.query.filter_by(user_id=current_user.id).first()
    if not company_link:
        flash("Vous n'êtes lié à aucune entreprise.", "danger")
        return redirect(url_for("admin_blueprint.sales"))

    # Vérifier que le point de vente appartient bien à la même entreprise
    company_salePoint = CompanyUser.query.filter_by(
        id=company_user_id,
        company_id=company_link.company_id
    ).first()

    if not company_salePoint:
        flash("Point de vente invalide ou non lié à votre entreprise.", "danger")
        return redirect(url_for("admin_blueprint.sales"))

    company_id = company_salePoint.company_id

    # Créer la dépense
    expense = Expense(
        company_id=company_id,
        company_user_id=company_salePoint.id,   # rattacher au bon point de vente
        name=name,
        amount=float(cost),                     # conversion en float
        created_at=datetime.utcnow()
    )
    db.session.add(expense)
    db.session.flush()  # pour générer expense.id

    # Créer un historique (AuditLog)
    log = AuditLog(
        company_id=company_id,
        actor_id=current_user.id,
        company_user_id=company_salePoint.id,   # rattacher au bon point de vente
        action_type="New Expense",
        entity=f"{expense.name}",
        entity_id=expense.id,
        sale_point=company_salePoint.sale_point,   # bon point de vente
        impact_value=float(cost),
        impact_unit="Currency",
        status="success",
        description=f"Added expense '{name}' with cost of {cost}",
        created_at=datetime.utcnow()
    )
    db.session.add(log)

    db.session.commit()

    flash("Dépense ajoutée avec succès !", "success")
    return redirect(url_for("admin_blueprint.sales"))

# pour ajouter une source de revenu via modal
@blueprint.route('/add-revenue', methods=["POST"])
@login_required
@company_required
@admin_required
@subscription_required
@csrf.exempt
def add_revenue():
    source = request.form.get("revenue_source")
    amount = request.form.get("revenue_amount")
    company_user_id = request.form.get("company_user_id")  # ID du point de vente choisi

    # Vérifier que l'utilisateur est lié à une entreprise
    company_link = CompanyUser.query.filter_by(user_id=current_user.id).first()
    if not company_link:
        flash("Vous n'êtes lié à aucune entreprise.", "danger")
        return redirect(url_for("admin_blueprint.sales"))

    # Vérifier que le point de vente appartient bien à la même entreprise
    company_salePoint = CompanyUser.query.filter_by(
        id=company_user_id,
        company_id=company_link.company_id
    ).first()

    if not company_salePoint:
        flash("Point de vente invalide ou non lié à votre entreprise.", "danger")
        return redirect(url_for("admin_blueprint.sales"))

    company_id = company_salePoint.company_id

    # Créer la source de revenu
    revenue = RevenueSource(
        company_id=company_id,
        company_user_id=company_salePoint.id,   # rattacher au bon point de vente
        name=source,
        amount=float(amount),                   # conversion en float
        created_at=datetime.utcnow()
    )
    db.session.add(revenue)
    db.session.flush()  # pour générer revenue.id

    # Créer un historique (AuditLog)
    log = AuditLog(
        company_id=company_id,
        actor_id=current_user.id,
        company_user_id=company_salePoint.id,   # rattacher au bon point de vente
        action_type="New Revenue",
        entity=f"{revenue.name}",
        entity_id=revenue.id,
        sale_point=company_salePoint.sale_point,   # bon point de vente
        impact_value=float(amount),
        impact_unit="Currency",
        status="success",
        description=f"Added revenue source '{source}' with amount of {amount}",
        created_at=datetime.utcnow()
    )
    db.session.add(log)
    generate_report_snapshot(company_id, company_salePoint.id)


    db.session.commit()

    flash("Source de revenu ajoutée avec succès !", "success")
    return redirect(url_for("admin_blueprint.sales"))

# pour ajouter un passif via modal
@blueprint.route("/add_liability", methods=["POST"])
@login_required
@company_required
@admin_required
@subscription_required
@csrf.exempt
def add_liability():
    user = User.query.filter_by(id=current_user.id).first()
    company_link = CompanyUser.query.filter_by(user_id=user.id).first()

    if not company_link:
        flash("You are not affiliated with any company.", "danger")
        return redirect(url_for("admin_blueprint.finance"))

    company_id = company_link.company_id

    # Récupérer les données du formulaire
    liability_names = request.form.getlist("liability_name[]")
    liability_values = request.form.getlist("liability_value[]")
    liability_types = request.form.getlist("liability_type[]")

    for name, value, ltype in zip(liability_names, liability_values, liability_types):
        if name and value and ltype:
            liability = Liability(
                company_id=company_id,
                type=ltype,
                name=name,
                value=float(value),
                created_at=datetime.utcnow()
            )
            db.session.add(liability)

            # Audit log
            log = AuditLog(
                company_id=company_id,
                company_user_id=company_link.id,
                actor_id=user.id,
                action_type="Add Liability",
                entity=name,
                entity_id=liability.id,
                sale_point=company_link.sale_point,
                impact_value=value,
                impact_unit="USD",
                status="success",
                description=f"Added liability '{name}' of {value} {company_link.company.currency}",
                created_at=datetime.utcnow()
            )
            db.session.add(log)

    db.session.commit()
    flash("Liability added successfully!", "success")
    return redirect(url_for("admin_blueprint.sales"))


# pour la page des administrateurs
@blueprint.route('/customers', methods=['POST', 'GET'])
@login_required
@company_required
@admin_required
@subscription_required
def customers():
    # Utilisateur connecté (CEO)
    user = User.query.get(current_user.id)

    # Lien vers sa company
    company_link = CompanyUser.query.filter_by(user_id=user.id, role="owner").first()
    if not company_link:
        flash("Vous n'êtes affilié à aucune entreprise.", "danger")
        return redirect(url_for("admin_blueprint.admin"))

    company = Company.query.get(company_link.company_id)

    company_subscription = CompanySubscription.query.filter_by(
        company_id=company_link.company_id,
        status="active"
    ).first()

    subscription_plan = company_subscription.plan if company_subscription else None

    # Tous les administrateurs de cette entreprise
    administrators = CompanyUser.query.filter_by(company_id=company.id, role="administrator").all()

    # Calculer la moyenne journalière pour chaque admin + récupérer le mot de passe temporaire
    admin_stats = []
    for admin_link in administrators:
        admin_user = User.query.get(admin_link.user_id)
        daily_avg = get_admin_daily_average(admin_user.id, company.id)

        temp_cred = TemporaryCredential.query.filter_by(user_id=admin_user.id).first()
        temp_password = temp_cred.password if temp_cred else None

        admin_stats.append({
            "id": admin_user.id,
            "name": admin_user.name,
            "email": admin_user.email,
            "sale_point": admin_link.sale_point,
            "daily_avg": daily_avg,
            "password": temp_password
        })

    return render_template(
        "admin/administrator.html",
        page_active="customers",
        company=company,
        administrators=admin_stats, 
        company_link=company_link,
        subscription_plan=subscription_plan
    )

# pour un nouvel administrateur
@blueprint.route('/add-administrator', methods=["POST"])
@login_required
@company_required
@admin_required
@subscription_required
@csrf.exempt
def add_administrator():
    name = request.form.get("name")
    email = request.form.get("email")
    sale_point = request.form.get("sale_point")
    phone_number = request.form.get("phone_number")

    # Vérifier si l'utilisateur existe déjà
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash("Un utilisateur avec cet email existe déjà.", "danger")
        return redirect(url_for("admin_blueprint.sales"))

    # Récupérer la company du owner connecté
    company_link = CompanyUser.query.filter_by(
        user_id=current_user.id,
        role="owner"
    ).first()

    if not company_link:
        flash("Vous n'êtes lié à aucune entreprise.", "danger")
        return redirect(url_for("admin_blueprint.customers"))

    # ================== LOGIQUE D'ABONNEMENT ==================

    active_subscription = CompanySubscription.query.filter_by(
        company_id=company_link.company_id,
        status="active"
    ).first()

    if not active_subscription:
        flash("Aucun abonnement actif trouvé.", "danger")
        return redirect(url_for("admin_blueprint.customers"))

    plan_name = active_subscription.plan.name

    # Définir les limites
    if plan_name == "Growth":
        max_admins = 5
    elif plan_name == "Enterprise":
        max_admins = 15
    elif plan_name == "Corporate":
        max_admins = None  # Illimité
    else:
        max_admins = 0  # Sécurité

    # Compter les administrateurs existants
    current_admin_count = CompanyUser.query.filter_by(
        company_id=company_link.company_id,
        role="administrator"
    ).count()

    if max_admins is not None and current_admin_count >= max_admins:
        flash(f"Limite atteinte pour le plan {plan_name}. Maximum {max_admins} administrateurs.", "danger")
        return redirect(url_for("admin_blueprint.customers"))

    # ================== CREATION ADMIN ==================

    alphabet = string.ascii_letters + string.digits
    random_password = ''.join(secrets.choice(alphabet) for _ in range(8))
    password_hash = bcrypt.generate_password_hash(random_password)

    new_user = User(
        email=email,
        name=name,
        password_hash=password_hash,
        is_active=True,
        created_at=datetime.utcnow()
    )

    db.session.add(new_user)
    db.session.flush()

    new_company_user = CompanyUser(
        user_id=new_user.id,
        company_id=company_link.company_id,
        role="administrator",
        sale_point=sale_point,
        created_at=datetime.utcnow()
    )

    db.session.add(new_company_user)

    temp_cred = TemporaryCredential(
        user_id=new_user.id,
        password=random_password,
        created_at=datetime.utcnow()
    )

    db.session.add(temp_cred)

    log = AuditLog(
        company_id=company_link.company_id,
        actor_id=current_user.id,
        company_user_id=company_link.id,
        action_type="New Administrator",
        entity=f"{new_user.name}",
        entity_id=new_user.id,
        sale_point=company_link.sale_point,
        impact_value=0,
        impact_unit="Units",
        status="success",
        description=f"Added administrator '{name}' with email '{email}'",
        created_at=datetime.utcnow()
    )

    db.session.add(log)

    db.session.commit()

    flash(f"Administrateur ajouté avec succès ! Mot de passe temporaire : {random_password}", "success")
    return redirect(url_for("admin_blueprint.customers"))

# pour modifier un administrateur
@blueprint.route('/edit-administrator', methods=["POST"])
@login_required
@company_required
@admin_required
@subscription_required
@csrf.exempt
def edit_administrator():
    admin_id = request.form.get("admin_id")
    name = request.form.get("name")
    email = request.form.get("email")
    sale_point = request.form.get("sale_point")

    # Vérifier que l'admin existe
    admin_user = User.query.get(admin_id)
    if not admin_user:
        flash("Administrator not found.", "danger")
        return redirect(url_for("admin_blueprint.customers"))

    # Vérifier que le CEO est bien lié à une company
    company_link = CompanyUser.query.filter_by(user_id=current_user.id, role="owner").first()
    if not company_link:
        flash("You are not linked to any company.", "danger")
        return redirect(url_for("admin_blueprint.customers"))

    # Vérifier que l'admin appartient à cette company
    company_user = CompanyUser.query.filter_by(user_id=admin_user.id, company_id=company_link.company_id).first()
    if not company_user:
        flash("This administrator does not belong to your company.", "danger")
        return redirect(url_for("admin_blueprint.customers"))

    # Mettre à jour les infos de l'utilisateur (sans toucher au mot de passe)
    admin_user.name = name
    admin_user.email = email

    # Mettre à jour le sale_point
    company_user.sale_point = sale_point

    # Créer un historique (AuditLog)
    log = AuditLog(
        company_id=company_link.company_id,
        actor_id=current_user.id,
        company_user_id=company_link.id,
        action_type="Update Administrator",                 # type d’action
        entity=f"{admin_user.name}",                     # module concerné
        entity_id=admin_user.id,                 # ID du produit créé
        sale_point=company_link.sale_point,   # point de vente
        impact_value=0,                # impact sur le stock (0 car pas de stock ici)
        impact_unit="Units",                  # unité
        status="success",                     # statut
        description=f"Updated administrator '{name}' with email '{email}'",
        created_at=datetime.utcnow()
    )
    db.session.add(log)

    db.session.commit()

    flash("Administrator updated successfully!", "success")
    return redirect(url_for("admin_blueprint.customers"))

# pour supprimer un administrateur
@blueprint.route('/delete-administrator', methods=["POST"])
@login_required
@company_required
@admin_required
@subscription_required
@csrf.exempt
def delete_administrator():
    admin_id = request.form.get("admin_id")

    admin_user = User.query.get(admin_id)
    if not admin_user:
        flash("Administrator not found.", "danger")
        return redirect(url_for("admin_blueprint.customers"))

    # CEO → company
    company_link = CompanyUser.query.filter_by(
        user_id=current_user.id,
        role="owner"
    ).first()

    if not company_link:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("admin_blueprint.customers"))

    # Admin → same company
    company_user = CompanyUser.query.filter_by(
        user_id=admin_user.id,
        company_id=company_link.company_id,
        role="administrator"
    ).first()

    if not company_user:
        flash("This administrator does not belong to your company.", "danger")
        return redirect(url_for("admin_blueprint.customers"))

    # 🔥 SUPPRESSION
    TemporaryCredential.query.filter_by(user_id=admin_user.id).delete()
    db.session.delete(company_user)

    # ⚠️ OPTION :
    # si l’admin n’appartient à aucune autre company → supprimer le User
    still_linked = CompanyUser.query.filter_by(user_id=admin_user.id).count()
    if still_linked == 0:
        db.session.delete(admin_user)

    # Créer un historique (AuditLog)
    log = AuditLog(
        company_id=company_link.company_id,
        actor_id=current_user.id,
        company_user_id=company_link.id,
        action_type="Deleting Administrator",                 # type d’action
        entity=f"{admin_user.name}",                     # module concerné
        entity_id=admin_user.id,                 # ID du produit créé
        sale_point=company_link.sale_point,   # point de vente
        impact_value=0,                # impact sur le stock (0 car pas de stock ici)
        impact_unit="Units",                  # unité
        status="success",                     # statut
        description=f"Deleted administrator '{admin_user.name}' with email '{admin_user.email}'",
        created_at=datetime.utcnow()
    )
    db.session.add(log)


    db.session.commit()

    flash("Administrator deleted successfully.", "success")
    return redirect(url_for("admin_blueprint.customers"))

# pour la page de rapports
@blueprint.route('/reports', methods=['POST', 'GET'])
@login_required
@company_required
@admin_required
@subscription_required
def reports():
    user = User.query.filter_by(id=current_user.id).first()
    company_link = CompanyUser.query.filter_by(user_id=user.id).first()

    if not company_link:
        flash("You are not linked to any company.", "danger")
        return redirect(url_for("admin_blueprint.admin"))
    
    company_subscription = CompanySubscription.query.filter_by(
        company_id=company_link.company_id,
        status="active"
    ).first()

    subscription_plan = company_subscription.plan if company_subscription else None

    # Récupérer tous les logs de la company
    logs = AuditLog.query.filter_by(company_id=company_link.company_id).order_by(AuditLog.created_at.desc()).all()

    return render_template(
        'admin/reports.html',
        page_active="reports",
        user=user,
        company_link=company_link,
        logs=logs,
        subscription_plan=subscription_plan
    )

# pour la page de notifications
@blueprint.route('/notifications', methods=['POST', 'GET'])
@login_required
@company_required
@admin_required
@subscription_required
def notifications():
    user = User.query.filter_by(id=current_user.id).first()
    note = Notifications.query.filter_by(user_id=user.id).order_by(Notifications.created_at.desc()).all()
    company_link = CompanyUser.query.filter_by(user_id=user.id, role="owner").first()

    company_subscription = CompanySubscription.query.filter_by(
        company_id=company_link.company_id,
        status="active"
    ).first()

    subscription_plan = company_subscription.plan if company_subscription else None

    return render_template(
        'admin/notifications.html', 
        page_active="notifications", note=note, 
        user=user, company_link=company_link,
        subscription_plan=subscription_plan
        )

# pour la page de support
@blueprint.route('/support', methods=['POST', 'GET'])
@login_required
@company_required
@subscription_required
def support():
    user = User.query.filter_by(id=current_user.id).first()
    company_link = CompanyUser.query.filter_by(user_id=user.id, role="owner").first()

    company_subscription = CompanySubscription.query.filter_by(
        company_id=company_link.company_id,
        status="active"
    ).first()

    subscription_plan = company_subscription.plan if company_subscription else None

    return render_template(
        'admin/support.html', page_active="support", 
        user=user, company_link=company_link,
        subscription_plan=subscription_plan
        )

# pour la page de profile
@blueprint.route('/profile', methods=['POST', 'GET'])
@login_required
@company_required
@subscription_required
def profile():
    user = User.query.filter_by(id=current_user.id).first()
    company_link = CompanyUser.query.filter_by(user_id=user.id).first()
    sale_point = CompanyUser.query.filter_by(user_id=user.id,
        company_id=company_link.company_id
    ).first()

    company_subscription = CompanySubscription.query.filter_by(
        company_id=company_link.company_id,
        status="active"
    ).first()

    subscription_plan = company_subscription.plan if company_subscription else None

    return render_template(
        'admin/profile.html', page_active="profile", 
        user=user, company_link=company_link, sale_point=sale_point,
        subscription_plan=subscription_plan
        )

# vente par un agent
@blueprint.route("/add-sale", methods=["POST"])
@login_required
@company_required
@subscription_required
@csrf.exempt
def add_sale():
    product_id = request.form.get("product_id")
    quantity = int(request.form.get("quantity"))

    product = Product.query.get_or_404(product_id)

    # Vérifier le point de vente lié au produit
    company_salePoint = CompanyUser.query.get(product.company_user_id)
    if not company_salePoint:
        flash("Invalid point of sale.", "danger")
        return redirect(url_for("admin_blueprint.sales"))

    # Vérifier stock actuel
    current_stock = get_product_stock(product.id, product.company_id)
    if quantity > current_stock:
        flash("Not enough stock available.", "danger")
        return redirect(url_for("admin_blueprint.sales"))

    # Créer mouvement d'inventaire (sortie de stock)
    inventory_movement = InventoryMovement(
        product_id=product.id,
        company_id=product.company_id,
        company_user_id=company_salePoint.id,
        actor_id=current_user.id,
        movement_type="sale",
        quantity=quantity,
        created_at=datetime.utcnow()
    )
    db.session.add(inventory_movement)

    # Créer un AuditLog
    log = AuditLog(
        company_id=product.company_id,
        actor_id=current_user.id,
        company_user_id=company_salePoint.id,
        action_type="Sale",
        entity=f"{product.name}",
        entity_id=product.id,
        sale_point=company_salePoint.sale_point,
        impact_value=quantity,
        impact_unit="Units",
        status="success",
        description=f"Sold {quantity} units of product '{product.name}'",
        created_at=datetime.utcnow()
    )
    db.session.add(log)

    generate_report_snapshot(product.company_id, company_salePoint.id)

    db.session.commit()

    flash("Sale recorded successfully!", "success")
    return redirect(url_for("admin_blueprint.sales"))

# depense pr point de vente
@blueprint.route('/add-expenses', methods=["POST"])
@login_required
@company_required
@subscription_required
@csrf.exempt
def add_expenses():
    name = request.form.get("expense_name")
    cost = request.form.get("expense_cost")

    # Vérifier que l'utilisateur est lié à une entreprise
    company_link = CompanyUser.query.filter_by(user_id=current_user.id).first()
    if not company_link:
        flash("Vous n'êtes lié à aucune entreprise.", "danger")
        return redirect(url_for("admin_blueprint.sales"))

    company_id = company_link.company_id

    # Créer la dépense (toujours rattachée au point de vente de l'agent connecté)
    expense = Expense(
        company_id=company_id,
        company_user_id=company_link.id,   # point de vente de l’agent
        name=name,
        amount=float(cost),
        created_at=datetime.utcnow()
    )
    db.session.add(expense)
    db.session.flush()  # pour générer expense.id

    # Créer un AuditLog
    log = AuditLog(
        company_id=company_id,
        actor_id=current_user.id,
        company_user_id=company_link.id,
        action_type="New Expense",
        entity=f"{expense.name}",
        entity_id=expense.id,
        sale_point=company_link.sale_point,   # point de vente de l’agent
        impact_value=float(cost),
        impact_unit="Currency",
        status="success",
        description=f"Added expense '{name}' with cost of {cost}",
        created_at=datetime.utcnow()
    )
    db.session.add(log)

    db.session.commit()

    flash("expense added successfully!", "success")
    return redirect(url_for("admin_blueprint.sales"))

# declarer un revenu par point de vente
@blueprint.route('/add-revenues', methods=["POST"])
@login_required
@company_required
@subscription_required
@csrf.exempt
def add_revenues():
    source = request.form.get("revenue_source")
    amount = request.form.get("revenue_amount")

    # Vérifier que l'utilisateur est lié à une entreprise
    company_link = CompanyUser.query.filter_by(user_id=current_user.id).first()
    if not company_link:
        flash("Vous n'êtes lié à aucune entreprise.", "danger")
        return redirect(url_for("admin_blueprint.sales"))

    company_id = company_link.company_id

    # Créer le revenu (toujours rattaché au point de vente de l'agent connecté)
    revenue = RevenueSource(
        company_id=company_id,
        company_user_id=company_link.id,   # point de vente de l’agent
        name=source,
        amount=float(amount),
        created_at=datetime.utcnow()
    )
    db.session.add(revenue)
    db.session.flush()  # pour générer revenue.id

    # Créer un AuditLog
    log = AuditLog(
        company_id=company_id,
        actor_id=current_user.id,
        company_user_id=company_link.id,
        action_type="New Revenue",
        entity=f"{revenue.name}",
        entity_id=revenue.id,
        sale_point=company_link.sale_point,   # point de vente de l’agent
        impact_value=float(amount),
        impact_unit=company_link.company.currency,
        status="success",
        description=f"Declared revenue '{source}' with amount of {amount}",
        created_at=datetime.utcnow()
    )
    db.session.add(log)
    generate_report_snapshot(company_id, company_link.id)

    db.session.commit()

    flash("Revenue declared successfully!", "success")
    return redirect(url_for("admin_blueprint.sales"))

# pour le rapport global mensuel (tous les points de vente confondus)
@blueprint.route("/api/reports")
@login_required
@company_required
@subscription_required
def api_reports():
    try:
        report_type = request.args.get("type")

        user = User.query.get(current_user.id)
        company_link = CompanyUser.query.filter_by(user_id=user.id).first_or_404()
        company_id = company_link.company_id

        if report_type == "revenue":
            return jsonify(get_revenue_report(company_id))

        if report_type == "expenses":
            return jsonify(get_expense_report(company_id))

        if report_type == "cashflow":
            return jsonify(get_cashflow_report(company_id))

        if report_type == "inventory":
            return jsonify(get_inventory_report(company_id))
    except Exception as e:
        print("API REPORT ERROR:", e)
        return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Unknown report type"}), 400

# statistique de des cartes globales
@blueprint.route('/dashboard_data_json')
def dashboard_data_json():
    # Récupère la compagnie de l'utilisateur connecté
    company_link = CompanyUser.query.filter_by(user_id=current_user.id).first()
    company_id = company_link.company_id if company_link else None

    if not company_id:
        return {"error": "User not linked to a company"}, 400

    # Exemple simple : somme de RevenueSource et Expense
    total_revenue = db.session.query(func.coalesce(func.sum(RevenueSource.amount), 0))\
        .filter(RevenueSource.company_id==company_id).scalar()
    total_expense = db.session.query(func.coalesce(func.sum(Expense.amount), 0))\
        .filter(Expense.company_id==company_id).scalar()
    net_profit = total_revenue - total_expense

    total_stock_units = db.session.query(func.coalesce(func.sum(Product.unit_price * InventoryMovement.quantity), 0))\
        .join(InventoryMovement, InventoryMovement.product_id==Product.id)\
        .filter(Product.company_id==company_id).scalar()

    low_stock_products = db.session.query(Product).join(InventoryMovement)\
        .filter(Product.company_id==company_id)\
        .group_by(Product.id)\
        .having(func.sum(InventoryMovement.quantity) < 10).count()  # seuil de stock faible

    return {
        "revenue": {"total": float(total_revenue), "growth_percent": 5},  # tu peux calculer vs last week
        "expense": {"total": float(total_expense)},
        "profit": {"net": float(net_profit)},
        "inventory": {"total_units": float(total_stock_units), "low_stock_products": low_stock_products}
    }
