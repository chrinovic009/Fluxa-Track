# -*- encoding: utf-8 -*-
"""
Init file for the admin blueprint
"""

from flask import Blueprint

blueprint = Blueprint(
    'admin_blueprint',
    __name__,
    url_prefix='/admin'  # toutes les routes commenceront par /admin...
)
