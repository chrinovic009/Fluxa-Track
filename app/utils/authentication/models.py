from app.extensions import db, bcrypt
from flask_login import UserMixin
from datetime import datetime

# ======================================================= TABLES DES DONNEES ============================================================ #

# Modèle utilisateur
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255))
    family_name = db.Column(db.String(255))

    password_hash = db.Column(db.String(255), nullable=True)

    auth_provider = db.Column(
        db.Enum("local", "google", "apple", name="auth_provider"),
        default="local",
        nullable=False
    )

    google_id = db.Column(db.String(64), unique=True, nullable=True)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    companies = db.relationship("CompanyUser", back_populates="user")

# pour afficher en clair les mot de passe des administrateur:
class TemporaryCredential(db.Model):
    __tablename__ = "temporary_credentials"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Modèle d'entréprise
class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text)

    business_size = db.Column(
        db.Enum("personal", "small", "medium", "large", name="business_size"),
        nullable=False
    )

    legal_structure = db.Column(
        db.Enum("individual", "ets", "sarl", "sa", "ngo", "other", name="legal_structure"),
        nullable=False
    )

    industry = db.Column(db.String(100))
    currency = db.Column(db.String(3), nullable=False)

    report_period = db.Column(
        db.Enum("daily", "weekly", "monthly", name="report_period"),
        nullable=False
    )

    main_sales_point = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship("CompanyUser", back_populates="company")
    products = db.relationship("Product", back_populates="company")
    reports = db.relationship("ReportSnapshot", backref="company", lazy=True, cascade="all, delete-orphan")

# Modèle administrateur 
class CompanyUser(db.Model):
    __tablename__ = "company_users"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)

    role = db.Column(
        db.Enum("owner", "administrator", "viewer", name="company_role"),
        nullable=False
    )

    sale_point = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="companies")
    company = db.relationship("Company", back_populates="users")

    __table_args__ = (
        db.UniqueConstraint("user_id", "company_id", name="uq_user_company"),
    )

# Modèle produit
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    company_user_id = db.Column(db.Integer, db.ForeignKey("company_users.id"), nullable=False)

    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100))
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship("Company", back_populates="products")
    movements = db.relationship("InventoryMovement", back_populates="product")
    company_user = db.relationship("CompanyUser")

# Modèle inventaire
class InventoryMovement(db.Model):
    __tablename__ = "inventory_movements"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    company_user_id = db.Column(db.Integer, db.ForeignKey("company_users.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    movement_type = db.Column(
        db.Enum("initial", "in", "out", "adjustment", "sale", name="movement_type"),
        nullable=False
    )

    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship("Product", back_populates="movements")
    actor = db.relationship("User")
    company_user = db.relationship("CompanyUser")

# Modèle de source de revenu
class RevenueSource(db.Model):
    __tablename__ = "revenue_sources"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    company_user_id = db.Column(db.Integer, db.ForeignKey("company_users.id"), nullable=False)

    name = db.Column(db.String(255))
    amount = db.Column(db.Numeric(14, 2), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    company_user = db.relationship("CompanyUser")

# Modèle de depenses
class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    company_user_id = db.Column(db.Integer, db.ForeignKey("company_users.id"), nullable=False)

    name = db.Column(db.String(255))
    amount = db.Column(db.Numeric(14, 2), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company_user = db.relationship("CompanyUser")

# Modèle de rapport
class ReportSnapshot(db.Model):
    __tablename__ = "report_snapshots"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    company_user_id = db.Column(db.Integer, db.ForeignKey("company_users.id"), nullable=False)

    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)

    total_revenue = db.Column(db.Numeric(14, 2))
    total_expense = db.Column(db.Numeric(14, 2))
    net_result = db.Column(db.Numeric(14, 2))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    company_user = db.relationship("CompanyUser")

# Modèle d'historique
class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    company_user_id = db.Column(db.Integer, db.ForeignKey("company_users.id"), nullable=False)

    action_type = db.Column(db.String(100))
    entity = db.Column(db.String(100))
    entity_id = db.Column(db.Integer)

    sale_point = db.Column(db.String(255))
    impact_value = db.Column(db.Numeric(14, 2))
    impact_unit = db.Column(db.String(50))  # USD, Units
    status = db.Column(db.String(50))       # success, failed, approved

    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    actor = db.relationship("User")
    company_user = db.relationship("CompanyUser")

#pour les pactifs
class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)

    type = db.Column(
        db.Enum("stock", "cash", "immobilisation", name="asset_type"),
        nullable=False
    )
    name = db.Column(db.String(255))
    value = db.Column(db.Numeric(14, 2), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    company = db.relationship("Company")

# pourles passifs
class Liability(db.Model):
    __tablename__ = "liabilities"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)

    type = db.Column(
        db.Enum("debt", "loan", "other", name="liability_type"),
        nullable=False
    )
    name = db.Column(db.String(255))
    value = db.Column(db.Numeric(14, 2), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    company = db.relationship("Company")

# ======================================================================================================================================= #



# ==================================================== TABLE D'INTELLIGENCE METIER ====================================================== #

# Modèle de predicion glbale
class PredictionModel(db.Model):
    __tablename__ = "prediction_models"

    id = db.Column(db.Integer, primary_key=True)
    company_user_id = db.Column(db.Integer, db.ForeignKey("company_users.id"), nullable=False)
    name = db.Column(db.String(100))  # e.g. "sales_forecast_v1"
    model_type = db.Column(db.String(50))  # sales, inventory, cashflow
    algorithm = db.Column(db.String(100))  # LSTM, ARIMA, XGBoost
    version = db.Column(db.String(20))

    trained_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    company_user = db.relationship("CompanyUser")

# Modèle de predition de vente
class SalesPrediction(db.Model):
    __tablename__ = "sales_predictions"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    company_user_id = db.Column(db.Integer, db.ForeignKey("company_users.id"), nullable=False)

    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)

    predicted_quantity = db.Column(db.Float)
    predicted_revenue = db.Column(db.Numeric(14, 2))

    confidence_score = db.Column(db.Float)  # 0 → 1
    model_id = db.Column(db.Integer, db.ForeignKey("prediction_models.id"))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    company_user = db.relationship("CompanyUser")

# Modèle de predition d'inventaire
class InventoryPrediction(db.Model):
    __tablename__ = "inventory_predictions"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    company_user_id = db.Column(db.Integer, db.ForeignKey("company_users.id"), nullable=False)

    predicted_stockout_date = db.Column(db.Date)
    days_remaining = db.Column(db.Integer)

    confidence_score = db.Column(db.Float)
    model_id = db.Column(db.Integer, db.ForeignKey("prediction_models.id"))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    company_user = db.relationship("CompanyUser")

# Modèle de predition de flux
class CashFlowPrediction(db.Model):
    __tablename__ = "cashflow_predictions"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    company_user_id = db.Column(db.Integer, db.ForeignKey("company_users.id"), nullable=False)

    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)

    predicted_revenue = db.Column(db.Numeric(14, 2))
    predicted_expenses = db.Column(db.Numeric(14, 2))
    predicted_balance = db.Column(db.Numeric(14, 2))

    confidence_score = db.Column(db.Float)
    model_id = db.Column(db.Integer, db.ForeignKey("prediction_models.id"))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    company_user = db.relationship("CompanyUser")

# Modèle de predition d'anomalie
class Anomaly(db.Model):
    __tablename__ = "anomalies"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    company_user_id = db.Column(db.Integer, db.ForeignKey("company_users.id"), nullable=False)

    anomaly_type = db.Column(
        db.Enum("expense", "revenue", "inventory", name="anomaly_type")
    )

    entity_id = db.Column(db.Integer)
    severity = db.Column(db.Enum("low", "medium", "high", name="anomaly_severity"), nullable=False)

    description = db.Column(db.Text)
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)

    company_user = db.relationship("CompanyUser")

# ======================================================================================================================================= #

# Modèle pour les notifications client
class Notifications(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)  # success, danger, warning, info
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)  # Ajout du champ de lecture

    def to_dict(self):
        """Convertir l'objet Notification en dictionnaire JSON"""
        return {
            "id": self.id,
            "type": self.type,
            "message": self.message,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "is_read": self.is_read
        }

# ======================================================= TABLES D'ABONNEMENT ============================================================ #

# Plans d'abonnement créés par l'admin
class SubscriptionPlan(db.Model):
    __tablename__ = "subscription_plans"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(14, 2), nullable=False)
    billing_cycle = db.Column(
        db.Enum("monthly", "yearly", name="billing_cycle"),
        nullable=False
    )
    # Conditions d'accès
    allowed_legal_structures = db.Column(db.Text)  # JSON ou liste séparée par virgules
    allowed_industries = db.Column(db.Text)        # JSON ou liste séparée par virgules
    min_business_size = db.Column(
        db.Enum("personal", "small", "medium", "large", name="min_business_size"),
        nullable=True
    )
    max_business_size = db.Column(
        db.Enum("personal", "small", "medium", "large", name="max_business_size"),
        nullable=True
    )

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subscriptions = db.relationship("CompanySubscription", back_populates="plan")


# Abonnement choisi par une entreprise
class CompanySubscription(db.Model):
    __tablename__ = "company_subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    subscription_plan_id = db.Column(db.Integer, db.ForeignKey("subscription_plans.id"), nullable=False)

    status = db.Column(
        db.Enum("active", "inactive", "expired", "pending", name="subscription_status"),
        default="pending",
        nullable=False
    )
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    auto_renew = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship("Company")
    plan = db.relationship("SubscriptionPlan", back_populates="subscriptions")
    payments = db.relationship("PaymentTransaction", back_populates="subscription")


# Règles optionnelles pour affiner les conditions
class SubscriptionRule(db.Model):
    __tablename__ = "subscription_rules"

    id = db.Column(db.Integer, primary_key=True)
    subscription_plan_id = db.Column(db.Integer, db.ForeignKey("subscription_plans.id"), nullable=False)

    condition_type = db.Column(
        db.Enum("legal_structure", "industry", "business_size", name="condition_type"),
        nullable=False
    )
    condition_value = db.Column(db.String(255), nullable=False)
    action = db.Column(
        db.Enum("allow", "deny", "require_upgrade", name="rule_action"),
        nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    plan = db.relationship("SubscriptionPlan")


# Historique des paiements liés aux abonnements
class PaymentTransaction(db.Model):
    __tablename__ = "payment_transactions"

    id = db.Column(db.Integer, primary_key=True)
    company_subscription_id = db.Column(db.Integer, db.ForeignKey("company_subscriptions.id"), nullable=False)

    amount = db.Column(db.Numeric(14, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    status = db.Column(
        db.Enum("paid", "pending", "failed", name="payment_status"),
        default="pending",
        nullable=False
    )
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)

    subscription = db.relationship("CompanySubscription", back_populates="payments")

# ======================================================================================================================================= #

# pour les erreurs de l'application
class SystemErrorLog(db.Model):
    __tablename__ = "system_error_logs"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)

    error_type = db.Column(
        db.Enum(
            "application",
            "database",
            "external_api",
            "timeout",
            name="system_error_type"
        ),
        nullable=False
    )

    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship("Company")

