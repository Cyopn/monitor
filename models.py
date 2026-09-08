from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from flask_login import UserMixin
import json


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False,
                     default='user')  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship to services
    services = db.relationship(
        'Service', backref='owner', lazy=True, cascade='all, delete-orphan')

    def get_id(self):
        return str(self.id)

    @property
    def is_admin(self):
        return self.role == 'admin'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    # e.g., "npm start" or "python app.py"
    command = db.Column(db.String(200), nullable=False)
    working_directory = db.Column(db.String(500), nullable=False)
    environment_vars = db.Column(db.Text)  # JSON string of key-value pairs
    npm_bin_path = db.Column(db.String(500))  # Path to npm binary (optional)
    node_path = db.Column(db.String(500))     # Path to node binary (optional)
    # Python environment variable (e.g., VIRTUAL_ENV path)
    python_env_var = db.Column(db.String(200))
    # Port for health checking (if applicable)
    port = db.Column(db.Integer)
    pid = db.Column(db.Integer)              # Current process ID
    # stopped, running, paused, error
    status = db.Column(db.String(20), default='stopped')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Properties for easier environment vars handling
    @property
    def env_vars_dict(self):
        if self.environment_vars:
            try:
                return json.loads(self.environment_vars)
            except json.JSONDecodeError:
                return {}
        return {}

    @env_vars_dict.setter
    def env_vars_dict(self, value):
        self.environment_vars = json.dumps(value) if value else '{}'

    def __repr__(self):
        return f'<Service {self.name}>'


class AppSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    npm_bin_path = db.Column(db.String(500))
    node_path = db.Column(db.String(500))
    python_env_path = db.Column(db.String(500))
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_current(cls):
        settings = cls.query.first()
        if settings is None:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings
