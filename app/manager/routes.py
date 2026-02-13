from app import db, UPLOAD_FOLDER, csrf, socketio, bcrypt
from flask import current_app, render_template, flash, redirect, url_for, jsonify, request
from app.utils.manager import blueprint
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from app.utils.decorator.company import super_admin_required

from app.utils.authentication.models import (
                                            User, Company, Notifications,
                                            CompanyUser, Product, InventoryMovement, RevenueSource, 
                                            Expense, TemporaryCredential, AuditLog, Asset, Liability,
                                            SubscriptionPlan, SubscriptionRule, CompanySubscription, PaymentTransaction,
                                            ReportSnapshot, SystemErrorLog
                                            )

# Route pour le dashboard du manager
@blueprint.route('/manager')
@login_required
@super_admin_required
def manager():
    # Nombre total d'entreprises
    total_companies = Company.query.count()

    # Abonnements actifs
    active_subscriptions = CompanySubscription.query.filter_by(status="active").count()

    # Abonnements inactifs
    inactive_subscriptions = CompanySubscription.query.filter_by(status="inactive").count()

    # Somme de toutes les transactions 
    total_budget = db.session.query(func.coalesce(func.sum(PaymentTransaction.amount), 0)).scalar()

    return render_template(
        'manager/manager.html',
        page_active='manager',
        total_companies=total_companies,
        active_subscriptions=active_subscriptions,
        inactive_subscriptions=inactive_subscriptions,
        total_budget=total_budget
    )

# pour le graphique des entrepises par secteur d'activité
@blueprint.route("/companies_by_sector")
@login_required
@super_admin_required
def companies_by_sector():
    # Regrouper les entreprises par secteur
    sectors = db.session.query(
        Company.industry, db.func.count(Company.id)
    ).group_by(Company.industry).all()

    labels = [s[0] for s in sectors]
    data = [s[1] for s in sectors]

    return jsonify({"labels": labels, "data": data})

# pour le graphique des abonnements actifs vs inactifs
@blueprint.route("/subscriptions_status")
@login_required
@super_admin_required
def subscriptions_status():
    active = CompanySubscription.query.filter_by(status="active").count()
    inactive = CompanySubscription.query.filter_by(status="inactive").count()

    return jsonify({
        "labels": ["Active", "Inactive"],
        "data": [active, inactive]
    })

# pour le graphique des renouvellements à venir
@blueprint.route("/upcoming_renewals")
@login_required
@super_admin_required
def upcoming_renewals():
    # Exemple: abonnements qui expirent dans les 30 prochains jours
    cutoff = datetime.utcnow() + timedelta(days=30)
    renewals = CompanySubscription.query.filter(
        CompanySubscription.end_date <= cutoff,
        CompanySubscription.status == "active"
    ).count()

    return jsonify({
        "labels": ["Upcoming Renewals"],
        "data": [renewals]
    })

# route pour la gestion des abonnements (liste, détails, etc.)
@blueprint.route("/subscription")
@login_required
@super_admin_required
def subscription():
    subscriptions = SubscriptionPlan.query.all()
    return render_template(
                        "manager/subscription.html",
                        page_active='subscription',
                        subscriptions=subscriptions)

# pour ajouter un nouvel abonnement
@blueprint.route("/add_subscription", methods=["POST"])
@login_required
@super_admin_required
@csrf.exempt
def add_subscription():
    try:
        new_plan = SubscriptionPlan(
            name=request.form.get("category"),  # catégorie devient le nom
            description=request.form.get("description"),
            price=request.form.get("price"),
            billing_cycle=request.form.get("billing_cycle"),
            allowed_legal_structures=request.form.get("allowed_legal_structures"),
            allowed_industries=request.form.get("allowed_industries"),
            min_business_size=request.form.get("min_business_size") or None,
            max_business_size=request.form.get("max_business_size") or None,
            is_active=True
        )
        db.session.add(new_plan)
        db.session.commit()

        # AuditLog pour tracer l'action
        audit = AuditLog(
            company_id=None,
            actor_id=current_user.id,
            company_user_id=current_user.companies[0].id if current_user.companies else None,
            action_type="create",
            entity="SubscriptionPlan",
            entity_id=new_plan.id,
            status="success",
            description=f"Created subscription plan {new_plan.name} with price {new_plan.price}"
        )
        db.session.add(audit)
        db.session.commit()

        flash("Subscription plan added successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding subscription: {e}", "danger")

    return redirect(url_for("man_blueprint.subscription"))

# pour modifier un abonnement existant
@blueprint.route("/edit_subscription/<int:sub_id>", methods=["POST"])
@login_required
@super_admin_required
@csrf.exempt
def edit_subscription(sub_id):
    try:
        plan = SubscriptionPlan.query.get_or_404(sub_id)

        # Mettre à jour les champs depuis le formulaire
        plan.name = request.form.get("name")  # <-- maintenant le nom est mis à jour
        plan.price = request.form.get("price")
        plan.billing_cycle = request.form.get("billing_cycle")
        plan.allowed_legal_structures = request.form.get("allowed_legal_structures")
        plan.allowed_industries = request.form.get("allowed_industries")
        plan.min_business_size = request.form.get("min_business_size") or None
        plan.max_business_size = request.form.get("max_business_size") or None
        plan.description = request.form.get("description")

        db.session.commit()

        # AuditLog
        audit = AuditLog(
            company_id=None,
            actor_id=current_user.id,
            company_user_id=current_user.companies[0].id if current_user.companies else None,
            action_type="update",
            entity="SubscriptionPlan",
            entity_id=plan.id,
            status="success",
            description=f"Updated subscription plan {plan.name}"
        )
        db.session.add(audit)
        db.session.commit()

        flash("Subscription updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating subscription: {e}", "danger")

    return redirect(url_for("man_blueprint.subscription"))

# pour supprimer un abonnement
@blueprint.route("/delete_subscription/<int:sub_id>", methods=["POST"])
@login_required
@super_admin_required
@csrf.exempt
def delete_subscription(sub_id):
    try:
        plan = SubscriptionPlan.query.get_or_404(sub_id)
        db.session.delete(plan)
        db.session.commit()

        # AuditLog
        audit = AuditLog(
            company_id=None,
            actor_id=current_user.id,
            company_user_id=current_user.companies[0].id if current_user.companies else None,
            action_type="delete",
            entity="SubscriptionPlan",
            entity_id=sub_id,
            status="success",
            description=f"Deleted subscription plan {plan.name}"
        )
        db.session.add(audit)
        db.session.commit()

        flash("Subscription deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting subscription: {e}", "danger")

    return redirect(url_for("man_blueprint.subscription"))

# pour la gestion des entreprises
@blueprint.route("/company")
@login_required
@super_admin_required
def company():
    companies = Company.query.all()
    # Abonnements actifs
    active_subscriptions = CompanySubscription.query.filter_by(status="active").count()
    total_companies = Company.query.count()

    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    active_company_ids = db.session.query(InventoryMovement.company_id)\
        .filter(InventoryMovement.created_at >= seven_days_ago)\
        .distinct()

    active_company_ids = active_company_ids.union(
        db.session.query(RevenueSource.company_id)
        .filter(RevenueSource.created_at >= seven_days_ago)
    ).union(
        db.session.query(Expense.company_id)
        .filter(Expense.created_at >= seven_days_ago)
    )

    inactive_companies_count = Company.query\
        .filter(~Company.id.in_(active_company_ids))\
        .count()
    
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    requests_last_hour = AuditLog.query\
        .filter(AuditLog.created_at >= one_hour_ago)\
        .count()

    avg_requests_per_minute = round(requests_last_hour / 60, 2)

    company_data = []

    for c in companies:

        # CEO
        ceo = next((cu.user for cu in c.users if cu.role == "owner"), None)

        # Abonnement actif
        subscription = CompanySubscription.query.filter_by(
            company_id=c.id,
            status="active"
        ).order_by(CompanySubscription.start_date.desc()).first()

        # Moyenne mensuelle des revenus
        avg_revenue = db.session.query(
            func.avg(ReportSnapshot.total_revenue)
        ).filter(
            ReportSnapshot.company_id == c.id
        ).scalar()

        # 🔹 Comptage des points de vente
        sale_points = set()
        for cu in c.users:
            if cu.sale_point:
                sale_points.add(cu.sale_point)
        # Ajouter le main_sales_point si défini
        if c.main_sales_point:
            sale_points.add(c.main_sales_point)

        total_sale_points = len(sale_points)

        company_data.append({
            "company": c,
            "ceo": ceo,
            "subscription": subscription,
            "avg_revenue": float(avg_revenue) if avg_revenue else 0,
            "total_sale_points": total_sale_points
        })

    return render_template(
        "manager/company.html",
        page_active="company",
        company_data=company_data,
        active_subscriptions=active_subscriptions,
        total_companies=total_companies,
        inactive_companies_count=inactive_companies_count,
        avg_requests_per_minute=avg_requests_per_minute
    )

# activer ou désactiver une entreprise
@blueprint.route("/companie/<int:company_id>/toggle-subscription", methods=["POST"])
@login_required
@super_admin_required
@csrf.exempt
def toggle_subscription(company_id):

    subscription = CompanySubscription.query.filter_by(
        company_id=company_id
    ).order_by(CompanySubscription.start_date.desc()).first()

    if not subscription:
        flash("No subscription found.", "danger")
        return redirect(url_for("man_blueprint.company"))

    # Déterminer nouvelle valeur
    if subscription.status == "active":
        new_status = "inactive"
        subscription.auto_renew = False
    else:
        new_status = "active"

    subscription.status = new_status

    # 🔎 Récupérer company_user lié à l'acteur
    company_user = CompanyUser.query.filter_by(
        user_id=current_user.id,
        company_id=company_id
    ).first()

    # 🧠 Création du log
    audit_log = AuditLog(
        company_id=company_id,
        actor_id=current_user.id,
        company_user_id=company_user.id if company_user else None,
        action_type="subscription_toggle",
        entity="CompanySubscription",
        entity_id=subscription.id,
        status="success",
        description=f"Subscription changed to {new_status}",
        created_at=datetime.utcnow()
    )

    db.session.add(audit_log)
    db.session.commit()

    flash("Subscription updated successfully.", "success")
    return redirect(url_for("man_blueprint.company"))

# pour la route des rapports
@blueprint.route("/report")
@login_required
@super_admin_required
def report():
    companies = Company.query.all()

    # Récupération des filtres GET
    company_id = request.args.get("company_id", type=int)
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    try:
        query = AuditLog.query

        # 🔹 Filtre par entreprise
        if company_id:
            query = query.filter(AuditLog.company_id == company_id)

        # 🔹 Filtre date début
        if from_date:
            from_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
            query = query.filter(AuditLog.created_at >= from_date_obj)

        # 🔹 Filtre date fin
        if to_date:
            to_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
            query = query.filter(AuditLog.created_at <= to_date_obj)

        logs = query.order_by(AuditLog.created_at.desc()).limit(1000).all()

    except Exception as e:
        current_app.logger.error(f"Erreur récupération AuditLog: {e}")
        logs = []

    # Sécurisation pour le template
    safe_logs = []
    for log in logs:
        actor_name = log.actor.name if log.actor else "Unknown"
        actor_role = log.actor.role if log.actor else ""
        company_name = (
            log.company_user.company.name
            if log.company_user and log.company_user.company
            else f"ID {log.company_id}"
        )
        impact_value = log.impact_value if log.impact_value else 0
        impact_unit = log.impact_unit if log.impact_unit else ""
        status = log.status if log.status else "N/A"

        safe_logs.append({
            "created_at": log.created_at,
            "actor_name": actor_name,
            "actor_role": actor_role,
            "company_name": company_name,
            "action_type": log.action_type,
            "entity": log.entity,
            "sale_point": log.sale_point,
            "impact_value": impact_value,
            "impact_unit": impact_unit,
            "status": status
        })

    return render_template(
        "manager/report.html",
        page_active="report",
        logs=safe_logs,
        companies=companies
    )

# statistique de des cartes globales
@blueprint.route('/admin_dashboard_json')
def admin_dashboard_json():
    # Total companies
    total_companies = Company.query.count()

    # Active / Inactive subscriptions
    active_subscriptions = CompanySubscription.query.filter_by(status='active').count()
    inactive_subscriptions = CompanySubscription.query.filter(CompanySubscription.status != 'active').count()

    # Total budget = somme de tous les revenus - dépenses de toutes les entreprises
    total_revenue = db.session.query(func.coalesce(func.sum(RevenueSource.amount), 0)).scalar()
    total_expense = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).scalar()
    total_budget = total_revenue - total_expense

    return jsonify({
        "total_companies": total_companies,
        "active_subscriptions": active_subscriptions,
        "inactive_subscriptions": inactive_subscriptions,
        "total_budget": float(total_budget)
    })



























