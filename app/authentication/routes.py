from app.utils.authentication import blueprint
from app import db, UPLOAD_FOLDER, csrf, socketio, bcrypt
from dateutil.relativedelta import relativedelta
from flask import (
                    render_template, flash, redirect, 
                    url_for, jsonify, request, send_from_directory, 
                    abort, session
                    )
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_dance.contrib.google import make_google_blueprint, google
from app.utils.authentication.models import (
                    User, Company, Notifications, CompanyUser,
                    Product, InventoryMovement, RevenueSource, Expense,
                    Asset, Liability, SubscriptionPlan, CompanySubscription
                    )
from app.authentication.fonctions import generate_secure_password
from datetime import datetime, date
from app.utils.decorator.company import company_required
from app.admin.fonctions import generate_report_snapshot, get_balance_sheet


# pour la page de login
@blueprint.route("/login", methods=["GET", "POST"])
@csrf.exempt
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email, is_active=True).first()

        if not user or not user.password_hash:
            flash("Invalid credentials", "danger")
            return redirect(url_for("auth_blueprint.login"))

        if not bcrypt.check_password_hash(user.password_hash, password):
            flash("Invalid credentials", "danger")
            return redirect(url_for("auth_blueprint.login"))

        login_user(user)

        company_link = CompanyUser.query.filter_by(user_id=current_user.id).first()

        if company_link:
            return redirect(url_for("admin_blueprint.admin"))
        
        return redirect(url_for("home_blueprint.home")) if user.email != "chrinovicnyembo009@gmail.com" else redirect(url_for("man_blueprint.manager"))

    return render_template("auth/login.html", page_active="login")

@blueprint.route("/google_login")
def google_login():
    # Si l'utilisateur n'est pas encore autorisé par Google → redirection vers Google
    if not google.authorized:
        return redirect(url_for("google.login"))

    # Récupération des infos Google
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        abort(401)

    user_info = resp.json()
    email = user_info.get("email")
    name = user_info.get("given_name") or user_info.get("name")
    family_name = user_info.get("family_name")
    google_id = user_info.get("id")

    if not email or not google_id:
        abort(400)

    # Vérifie si l'utilisateur existe déjà
    user = User.query.filter_by(email=email).first()

    if not user:
        # Génère un mot de passe aléatoire
        raw_password = generate_secure_password()
        password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

        # Crée l'utilisateur
        user = User(
            email=email,
            name=name,
            family_name=family_name,
            google_id=google_id,
            auth_provider="google",
            password_hash=password_hash,
            is_active=True
        )
        db.session.add(user)
        db.session.flush()  # flush pour garantir que user.id est attribué

        # Crée une notification de bienvenue
        welcome_notification = Notifications(
            title="Update Password",
            user_id=user.id,  # maintenant user.id est garanti
            message=f"Your login password is: {raw_password}. Please keep it confidential and commit it to memory.",
            type="bi bi-info",
            created_at=datetime.utcnow()
        )
        db.session.add(welcome_notification)
        db.session.flush()  # flush pour attribuer l’ID de la notification

        # Émet la notification via SocketIO
        socketio.emit('new_notifications', {
            "id": welcome_notification.id,
            "message": welcome_notification.message,
            "type": welcome_notification.type,
            "date": welcome_notification.created_at.strftime("%d/%m/%Y %H:%M")
        }, namespace='/')

        # Commit final
        db.session.commit()

    # Connecte l'utilisateur
    login_user(user)
    return redirect(url_for("home_blueprint.home"))

# pour la page de création d'entreprise
@blueprint.route('/business', methods=["GET", "POST"])
@csrf.exempt
@login_required
def business():

    company_link = CompanyUser.query.filter_by(user_id=current_user.id).first()
    if company_link:
        flash("You already have a business.", "info")
        return redirect(url_for("admin_blueprint.admin"))

    # ==========================
    # GET → afficher formulaire
    # ==========================
    if request.method == "GET":
        plan_id = request.args.get("plan_id")
        selected_plan = None

        if plan_id:
            selected_plan = SubscriptionPlan.query.filter_by(
                id=plan_id,
                is_active=True
            ).first()

        return render_template(
            "auth/create-business.html",
            selected_plan=selected_plan,
            page_active="business"
        )

    # ==========================
    # POST → création entreprise
    # ==========================

    plan_id = request.form.get("subscription_plan_id")

    if not plan_id:
        flash("No subscription plan selected.", "danger")
        return redirect(url_for("auth_blueprint.pricing"))

    plan = SubscriptionPlan.query.filter_by(
        id=plan_id,
        is_active=True
    ).first()

    if not plan:
        flash("Invalid subscription plan.", "danger")
        return redirect(url_for("auth_blueprint.pricing"))

    # Données soumises
    business_size = request.form.get("business_size")
    legal_structure = request.form.get("legal_structure")
    industry = request.form.get("industry")

    # ==========================
    # VALIDATION PLAN ↔ ENTREPRISE
    # ==========================

    size_order = ["personal", "small", "medium", "large"]


    if business_size not in size_order:
        flash("Invalid business size.", "danger")
        return redirect(request.url)
    
    if plan.min_business_size not in size_order or \
    plan.max_business_size not in size_order:
        flash("Plan configuration error.", "danger")
        return redirect(url_for("auth_blueprint.pricing"))


    # Validation business_size min/max
    if plan.min_business_size:
        if size_order.index(business_size) < size_order.index(plan.min_business_size):
            flash("Business size too small for this plan.", "danger")
            return redirect(request.url)

    if plan.max_business_size:
        if size_order.index(business_size) > size_order.index(plan.max_business_size):
            flash("Business size exceeds this plan.", "danger")
            return redirect(request.url)

    # Validation legal_structure
    if plan.allowed_legal_structures:
        allowed_structures = [x.strip() for x in plan.allowed_legal_structures.split(",")]
        if legal_structure not in allowed_structures:
            flash("Legal structure not allowed for this plan.", "danger")
            return redirect(request.url)

    # Validation industry
    if plan.allowed_industries:
        allowed_industries = [x.strip() for x in plan.allowed_industries.split(",")]
        if industry not in allowed_industries:
            flash("Industry not allowed for this plan.", "danger")
            return redirect(request.url)

    # ==========================
    # CREATION ENTREPRISE
    # ==========================

    company = Company(
        name=request.form.get("company_name"),
        address=request.form.get("company_address"),
        business_size=business_size,
        legal_structure=legal_structure,
        industry=industry,
        currency=request.form.get("currency"),
        report_period=request.form.get("report_period"),
        main_sales_point=request.form.get("main_sales_point"),
        created_at=datetime.utcnow()
    )

    db.session.add(company)
    db.session.flush()

    # ==========================
    # LIEN USER ↔ COMPANY
    # ==========================

    company_user = CompanyUser(
        user_id=current_user.id,
        company_id=company.id,
        role="owner",
        sale_point=company.main_sales_point,
        created_at=datetime.utcnow()
    )

    db.session.add(company_user)
    db.session.flush()

    # ==========================
    # CREATION ABONNEMENT
    # ==========================

    start_date = datetime.utcnow()

    if plan.billing_cycle == "monthly":
        end_date = start_date + relativedelta(months=1)
    else:
        end_date = start_date + relativedelta(years=1)

    subscription = CompanySubscription(
        company_id=company.id,
        subscription_plan_id=plan.id,
        status="active",
        start_date=start_date,
        end_date=end_date,
        auto_renew=True
    )

    db.session.add(subscription)

    # ==========================
    # PRODUITS + INVENTAIRE
    # ==========================

    product_names = request.form.getlist("product_name[]")
    product_prices = request.form.getlist("product_price[]")
    product_quantities = request.form.getlist("product_quantity[]")
    product_categories = request.form.getlist("product_category[]")

    for name, price, qty, category in zip(
        product_names,
        product_prices,
        product_quantities,
        product_categories
    ):
        if name and price and qty:

            product = Product(
                company_id=company.id,
                company_user_id=company_user.id,
                name=name,
                category=category,
                unit_price=price,
                created_at=datetime.utcnow()
            )
            db.session.add(product)
            db.session.flush()

            inventory = InventoryMovement(
                product_id=product.id,
                company_id=company.id,
                company_user_id=company_user.id,
                actor_id=current_user.id,
                movement_type="initial",
                quantity=int(qty),
                created_at=datetime.utcnow()
            )
            db.session.add(inventory)

            asset = Asset(
                company_id=company.id,
                type="stock",
                name=f"Stock initial {name}",
                value=float(price) * int(qty),
                created_at=datetime.utcnow()
            )
            db.session.add(asset)

    # ==========================
    # SOURCES DE REVENUS
    # ==========================

    for name, amount in zip(
        request.form.getlist("revenue_source[]"),
        request.form.getlist("revenue_amount[]")
    ):
        if name and amount:
            db.session.add(RevenueSource(
                company_id=company.id,
                company_user_id=company_user.id,
                name=name,
                amount=amount,
                created_at=datetime.utcnow()
            ))
            generate_report_snapshot(company.id, company_user.id)

    # ==========================
    # DEPENSES
    # ==========================

    for name, cost in zip(
        request.form.getlist("expense_name[]"),
        request.form.getlist("expense_cost[]")
    ):
        if name and cost:
            db.session.add(Expense(
                company_id=company.id,
                company_user_id=company_user.id,
                name=name,
                amount=cost,
                created_at=datetime.utcnow()
            ))

    # ==========================
    # ACTIFS INITIAUX
    # ==========================

    if request.form.get("initial_cash"):
        db.session.add(Asset(
            company_id=company.id,
            type="cash",
            name="Trésorerie initiale",
            value=float(request.form.get("initial_cash")),
            created_at=datetime.utcnow()
        ))

    if request.form.get("initial_immobilisation"):
        db.session.add(Asset(
            company_id=company.id,
            type="immobilisation",
            name="Immobilisations initiales",
            value=float(request.form.get("initial_immobilisation")),
            created_at=datetime.utcnow()
        ))

    # ==========================
    # PASSIFS
    # ==========================

    for name, value, ltype in zip(
        request.form.getlist("liability_name[]"),
        request.form.getlist("liability_value[]"),
        request.form.getlist("liability_type[]")
    ):
        if name and value and ltype:
            db.session.add(Liability(
                company_id=company.id,
                type=ltype,
                name=name,
                value=float(value),
                created_at=datetime.utcnow()
            ))

    # ==========================
    # COMMIT FINAL
    # ==========================

    db.session.commit()

    flash("Entreprise et abonnement activés avec succès.", "success")
    return redirect(url_for("home_blueprint.loading"))

@blueprint.route("/logout")
@login_required
def logout():
    session.clear()  # vide la session Flask
    logout_user()
    return redirect(url_for("home_blueprint.home"))
