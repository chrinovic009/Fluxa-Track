# -*- encoding: utf-8 -*-
"""
Init file for the manager blueprint
"""

from flask import Blueprint

blueprint = Blueprint(
    'man_blueprint',
    __name__,
    url_prefix='/manager'  # toutes les routes commenceront par /manager...
)
