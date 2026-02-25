# -*- encoding: utf-8 -*-

from flask import Flask, request, g
import time

from app.utils.authentication.models import User
from sqlalchemy.exc import IntegrityError
from app.extensions import db, login_manager, migrate, bcrypt, socketio, mail, csrf
from importlib import import_module
import os
from app.utils.decorator.time import humanize_date
from flask_dance.contrib.google import make_google_blueprint, google
from app.error_handlers import register_error_handlers
import logging
from logging.handlers import RotatingFileHandler

api_meteo = os.getenv("API_METEO")

# Chemin où les images seront sauvegardées
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Limiter la taille max des fichiers (ex. 10 Mo)
MAX_CONTENT_LENGTH = 10 * 1024 * 1024


def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    socketio.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth_blueprint.login"
    login_manager.login_message_category = 'info'


def register_blueprints(app):
    for module_name in ('authentication', 'home', 'admin', 'manager'):
        module = import_module(f'app.{module_name}.routes')
        app.register_blueprint(module.blueprint)

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def register_custom_filters(app: Flask):
    app.jinja_env.filters['humanize_date'] = humanize_date


def create_app(config="app.config.Config"):
    app = Flask(__name__)

    # =========================
    # HTTP TIMER
    # =========================
    @app.before_request
    def start_timer():
        g.start_time = time.time()
    
    def create_default_admin():
        ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
        ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

        if not ADMIN_EMAIL or not ADMIN_PASSWORD:
            raise ValueError("ADMIN_EMAIL or ADMIN_PASSWORD not set")

        existing_user = User.query.filter_by(email=ADMIN_EMAIL).first()

        if existing_user:
            return False  # L'admin existe déjà

        hashed_password = bcrypt.generate_password_hash(ADMIN_PASSWORD).decode('utf-8')

        admin_user = User(
            email=ADMIN_EMAIL,
            name="Super",
            family_name="Admin",
            password_hash=hashed_password,
            auth_provider="local",
            is_active=True
        )

        db.session.add(admin_user)

        try:
            db.session.commit()
            return True  # Créé avec succès
        except IntegrityError:
            db.session.rollback()
            return False
    # =========================
    # AFTER REQUEST (LOG + SECURITY)
    # =========================
    @app.after_request
    def after_request_handler(response):

        # Logging HTTP
        if hasattr(g, "start_time"):
            duration = round((time.time() - g.start_time) * 1000, 2)

            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            if ip and "," in ip:
                ip = ip.split(",")[0].strip()

            method = request.method
            path = request.full_path
            status = response.status_code
            user_agent = request.user_agent.string

            app.logger.info(
                f"IP={ip} | METHOD={method} | PATH={path} | "
                f"STATUS={status} | TIME={duration}ms | UA={user_agent}"
            )

        # Security headers
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
        response.headers["Content-Security-Policy"] = "default-src *"

        return response

    app.config.from_object(config)
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB
    app.config["PROPAGATE_EXCEPTIONS"] = True

    register_extensions(app)
    register_blueprints(app)
    register_custom_filters(app)
    register_error_handlers(app)

    if not app.debug:

        if not os.path.exists("logs"):
            os.makedirs("logs")

        file_handler = RotatingFileHandler(
            "logs/system.log",
            maxBytes=100 * 1024 * 1024,
            backupCount=10
        )

        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s | %(pathname)s:%(lineno)d",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        file_handler.setFormatter(formatter)

        app.logger.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    # Google OAuth blueprint
    google_bp = make_google_blueprint(
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        scope=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ],
        redirect_to="auth_blueprint.google_login"
    )

    app.register_blueprint(google_bp, url_prefix="/authentication")

    with app.app_context():
        db.create_all()
        create_default_admin()

    @login_manager.user_loader
    def load_user(user_id):
        from app.utils.authentication.models import User
        return User.query.get(int(user_id))

    return app
