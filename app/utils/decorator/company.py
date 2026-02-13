from functools import wraps
from flask import redirect, url_for, flash, g, abort
from flask_login import current_user
from app.utils.authentication.models import CompanyUser 

def company_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("You must be logged in.", "danger")
            return redirect(url_for("auth_blueprint.login"))

        company_link = CompanyUser.query.filter_by(user_id=current_user.id).first()
        if not company_link:
            flash("You need to create a business first.", "warning")
            return redirect(url_for("auth_blueprint.business"))

        g.company_link = company_link  # accessible dans la route
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("You must be logged in.", "danger")
            return redirect(url_for("auth_blueprint.login"))

        company_link = CompanyUser.query.filter_by(user_id=current_user.id, role="owner").first()
        if not company_link:
            flash("For CEO only.", "warning")
            return redirect(url_for("admin_blueprint.sales"))

        g.company_link = company_link  # accessible dans la route
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)

        if current_user.email != "chrinovicnyembo009@gmail.com":
            abort(403)

        return f(*args, **kwargs)

    return decorated_function


