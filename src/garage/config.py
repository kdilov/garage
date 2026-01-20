# src/garage/config.py
"""Application configuration classes."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class BaseConfig:
    """Base configuration with shared defaults."""
    
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = 'json'
    
    # Storage
    STORAGE_BACKEND = 'local'
    STORAGE_PATH = 'static'
    
    # AWS S3
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
    S3_REGION = os.environ.get('S3_REGION', 'eu-west-2')
    S3_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    S3_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    S3_ENDPOINT_URL = os.environ.get('S3_ENDPOINT_URL')
    S3_PREFIX = 'garage-inventory'
    
    # Security
    PASSWORD_RESET_EXPIRY = 3600  # 1 hour
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@garage-inventory.com')
    MAIL_SUPPRESS_SEND = False


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    LOG_FORMAT = 'text'
    
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{BASE_DIR / "inventory.db"}'
    )
    
    STORAGE_BACKEND = os.environ.get('STORAGE_BACKEND', 'local')
    MAIL_SUPPRESS_SEND = True


class ProductionConfig(BaseConfig):
    """Production configuration."""
    
    DEBUG = False
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = 'json'
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    STORAGE_BACKEND = os.environ.get('STORAGE_BACKEND', 's3')
    
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Fix Heroku postgres:// URL scheme
    _database_url = os.environ.get('DATABASE_URL', '')
    if _database_url.startswith('postgres://'):
        _database_url = _database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _database_url
    
    @classmethod
    def init_app(cls, app):
        """Validate required production settings."""
        required = ['SECRET_KEY', 'SQLALCHEMY_DATABASE_URI']
        
        if app.config.get('STORAGE_BACKEND') == 's3':
            required.extend(['S3_BUCKET_NAME', 'S3_REGION'])
        
        missing = [key for key in required if not app.config.get(key)]
        if missing:
            raise ValueError(f"Missing required production config: {', '.join(missing)}")


class TestingConfig(BaseConfig):
    """Testing configuration."""
    
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'WARNING'
    LOG_FORMAT = 'text'
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    STORAGE_BACKEND = 'local'
    STORAGE_PATH = '/tmp/garage-test-storage'
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}


def get_config(config_name: str | None = None):
    """Get configuration class by name."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    return config.get(config_name, config['default'])
