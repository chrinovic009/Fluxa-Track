from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user
from datetime import datetime
from app.utils.authentication.models import CompanyUser, CompanySubscription
from app.extensions import db

def subscription_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        company_user = CompanyUser.query.filter_by(
            user_id=current_user.id
        ).first()

        if not company_user:
            flash("No company configured.", "danger")
            return redirect(url_for("auth_blueprint.business"))

        subscription = CompanySubscription.query.filter_by(
            company_id=company_user.company_id
        ).first()

        if not subscription:
            flash("No subscription found.", "danger")
            return redirect(url_for("auth_blueprint.pricing"))

        if subscription.end_date < datetime.utcnow():
            subscription.status = "expired"
            db.session.commit()
            flash("Subscription expired.", "warning")
            return redirect(url_for("auth_blueprint.pricing"))

        if subscription.status != "active":
            flash("Subscription inactive.", "danger")
            return redirect(url_for("auth_blueprint.pricing"))

        return f(*args, **kwargs)

    return decorated_function
