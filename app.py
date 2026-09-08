from flask import Flask, redirect, url_for
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from services import bp as services_bp
    app.register_blueprint(services_bp, url_prefix='/services')

    from admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from monitoring import bp as monitoring_bp, init_monitoring
    app.register_blueprint(monitoring_bp, url_prefix='/monitoring')

    # Initialize monitoring
    init_monitoring(app)

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('services.index'))
        return redirect(url_for('auth.login'))

    return app
