# -*- encoding: utf-8 -*-
"""
Configuration File
"""

import os
import random
import string
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

# ==========================================================
# Cloudinary Configuration
# ==========================================================

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# ==========================================================
# Base Configuration
# ==========================================================

class Config(object):
    basedir = os.path.abspath(os.path.dirname(__file__))

    # Assets
    ASSETS_ROOT = os.getenv('ASSETS_ROOT', '/static')

    # Secret Key
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        SECRET_KEY = ''.join(random.choice(string.ascii_letters) for _ in range(32))

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'db.sqlite3')
    )

    # ======================================================
    # Google OAuth
    # ======================================================

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    # Important pour environnement local
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # ======================================================
    # Session Security
    # ======================================================

    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

    # En HTTPS uniquement
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    # Durée session (1h)
    REMEMBER_COOKIE_DURATION = 3600


# ==========================================================
# Production
# ==========================================================

class ProductionConfig(Config):
    DEBUG = False

    # En production HTTPS obligatoire
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


# ==========================================================
# Debug (HTTPS local)
# ==========================================================

class DebugConfig(Config):
    DEBUG = True

    # Si tu restes en HTTPS local → laisse True
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


# ==========================================================
# Config Dictionary
# ==========================================================

config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig
}
