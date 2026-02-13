from app.utils.home import blueprint
from app import db, UPLOAD_FOLDER, csrf, socketio
from flask import render_template, flash, redirect, url_for, jsonify, request
from flask_login import current_user
from sqlalchemy import func
from app.utils.decorator.company import company_required

from app.utils.authentication.models import (
                                            SubscriptionPlan, Company, PaymentTransaction, CompanyUser,
                                            RevenueSource, Expense
                                            )


# ---------------------------------------------------------------------------- pour les pages ----------------------------------------------------------------#
# pour la page d'acceuil
@blueprint.route('/')
def home():
    # Nombre total d'entreprises
    total_companies = Company.query.count()

    # Somme de toutes les entrées (revenus)
    total_revenue = db.session.query(
        func.coalesce(func.sum(RevenueSource.amount), 0)
    ).scalar()

    # Somme de toutes les sorties (dépenses)
    total_expense = db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).scalar()

    # Résultat net
    total_finance = total_revenue + total_expense

    plan = SubscriptionPlan.query.all()

    # ========================
    # Vérification utilisateur
    # ========================
    user_dashboard_url = None

    if current_user.is_authenticated:
        # Vérifier si l'utilisateur est lié à une entreprise
        company_link = CompanyUser.query.filter_by(user_id=current_user.id).first()
        
        if company_link:
            user_dashboard_url = url_for("admin_blueprint.admin")
        elif current_user.email == "chrinovicnyemb009@gmail.com":
            user_dashboard_url = url_for("man_blueprint.manager")
        else:
            user_dashboard_url = url_for("home_blueprint.home")  # utilisateur sans entreprise
    else:
        user_dashboard_url = url_for("home_blueprint.home")  # non connecté

    return render_template(
        'home/index.html',
        page_active="home",
        plan=plan,
        total_companies=total_companies,
        total_finance=total_finance,
        user_dashboard_url=user_dashboard_url
    )

# actualisation de statistiques (nombre d'entreprises & total de transaction suivie)
@blueprint.route('/stats')
def stats():
    total_companies = Company.query.count()
    total_revenue = db.session.query(func.coalesce(func.sum(RevenueSource.amount), 0)).scalar()
    total_expense = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).scalar()
    total_finance = total_revenue + total_expense

    return {
        "total_companies": int(total_companies),
        "total_finance": float(total_finance)
    }

# actualisation de statistiques (tarification)
@blueprint.route('/plans_json')
def plans_json():
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    result = []

    for p in plans:
        result.append({
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "billing_cycle": p.billing_cycle,
            "allowed_legal_structures": p.allowed_legal_structures,
            "allowed_industries": p.allowed_industries,
            "max_business_size": p.max_business_size,
            "description": p.description
        })

    return {"plans": result}

# pour la page de chargement
@blueprint.route('/loading')
@company_required
def loading():
    flash("Your dashboard is being set up, please wait a minute or so while we get everything in order", "sucess")
    return render_template('auth/loading.html', page_active="loading")

# pour la page de politique de confidentialité
@blueprint.route('/privacy')
def privacy():

    return render_template('home/privacy.html', page_active="privacy")

# pour la page de termes et conditions
@blueprint.route('/conditions')
def conditions():

    return render_template('home/conditions.html', page_active="conditions")