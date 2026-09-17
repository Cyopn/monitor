import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + \
        os.path.join(os.path.abspath(os.path.dirname(__file__)),
                     'instance', 'service_manager.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get(
        'WTF_CSRF_SECRET_KEY') or 'csrf-secret-key'

    # Login configuration
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_SECURE = False  # Set to True in production with HTTPS
    REMEMBER_COOKIE_HTTPONLY = True

    # Service monitoring
    SERVICE_CHECK_INTERVAL = 30  # seconds
    SERVICE_TIMEOUT = 10  # seconds for health check
    SERVICE_LOG_DIR = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'instance', 'logs'
    )

    # File uploads (if needed in future)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
