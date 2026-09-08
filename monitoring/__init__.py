from flask import Blueprint

bp = Blueprint('monitoring', __name__)

from . import routes  # noqa

# Import init_monitoring function for easy access
from .routes import init_monitoring