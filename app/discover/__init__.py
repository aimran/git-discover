from flask import Blueprint

discover = Blueprint('discover', __name__)

from . import routes

