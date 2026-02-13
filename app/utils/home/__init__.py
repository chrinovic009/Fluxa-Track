# -*- encoding: utf-8 -*-
"""
Init file for the home blueprint
"""

from flask import Blueprint

blueprint = Blueprint(
    'home_blueprint',
    __name__,
    url_prefix='/'  # toutes les routes commenceront par /...
)
