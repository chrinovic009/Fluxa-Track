# -*- encoding: utf-8 -*-
"""
Init file for the authentication blueprint
"""

from flask import Blueprint

blueprint = Blueprint(
    'auth_blueprint',
    __name__,
    url_prefix='/authentication'  # toutes les routes commenceront par /log...
)
