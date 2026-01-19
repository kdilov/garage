# src/garage/config.py
"""
Application configuration classes.

WHY THIS PATTERN:
- Different environments need different settings (you don't want DEBUG=True in production!)
- Class-based config allows inheritance (DevelopmentConfig extends BaseConfig)
- Environment variables keep secrets out of your code repository
- Type hints and defaults make configuration self-documenting

HOW TO USE:
- Set FLASK_ENV=development|production|testing
- Override any setting with environment variables
- For S3: Set STORAGE_BACKEND=s3 and provide AWS credentials
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class BaseConfig:
    """
    Base configuration with sensible defaults.
    
    All other configs inherit from this, so changes here affect everything.
    Only put settings here that are the same across all environments.
    """
    
    # SECURITY
    # In production, this MUST be set via environment variable
    # A weak secret key allows session hijacking attacks
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # DATABASE
    # Disable modification tracking - it uses extra memory and we don't need it
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # LOGGING
    # These are overridden per environment below
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = 'json'  # 'json' for production, 'text' for development
    
    # STORAGE
    # 'local' stores files on disk, 's3' stores in AWS S3
    STORAGE_BACKEND = 'local'
    STORAGE_PATH = 'static'
    
    # AWS S3 CONFIGURATION (only used when STORAGE_BACKEND='s3')
    # These replace your Cloudinary settings
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
    S3_REGION = os.environ.get('S3_REGION', 'eu-west-2')  # London region
    S3_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    S3_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    S3_ENDPOINT_URL = os.environ.get('S3_ENDPOINT_URL')  # For LocalStack testing
    S3_PREFIX = 'garage-inventory'  # All files stored under this prefix
    
    # PASSWORD RESET
    PASSWORD_RESET_EXPIRY = 3600  # 1 hour in seconds
    
    # FILE UPLOADS
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # EMAIL (keeping your existing mail settings pattern)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@garage-inventory.com')
    MAIL_SUPPRESS_SEND = False


class DevelopmentConfig(BaseConfig):
    """
    Development configuration - optimized for local development.
    
    Key differences from production:
    - DEBUG=True gives you the interactive debugger
    - Human-readable logs instead of JSON
    - Emails print to console instead of sending
    - SQLite database file for simplicity
    """
    
    DEBUG = True
    
    # Readable logs during development
    LOG_LEVEL = 'DEBUG'
    LOG_FORMAT = 'text'
    
    # SQLite file in instance/ folder
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{BASE_DIR / "inventory.db"}'
    )
    
    # Can override to test S3 locally
    STORAGE_BACKEND = os.environ.get('STORAGE_BACKEND', 'local')
    
    # Don't actually send emails - print them instead
    MAIL_SUPPRESS_SEND = True


class ProductionConfig(BaseConfig):
    """
    Production configuration - optimized for security and performance.
    
    Key differences from development:
    - DEBUG=False (NEVER enable debug in production - security risk!)
    - JSON logs for log aggregation services
    - S3 storage for scalability
    - Secure cookie settings
    """
    
    DEBUG = False
    
    # Structured logging for CloudWatch/Datadog/etc
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = 'json'
    
    # Database URL MUST be set in production
    # Typically PostgreSQL: postgresql://user:pass@host:5432/dbname
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Use S3 in production for scalability
    STORAGE_BACKEND = os.environ.get('STORAGE_BACKEND', 's3')
    
    # Security: cookies only sent over HTTPS
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    @classmethod
    def init_app(cls, app):
        """
        Production-specific initialization.
        
        Validates that required settings are configured.
        Fails fast if something is missing - better than cryptic errors later.
        """
        required = ['SECRET_KEY', 'SQLALCHEMY_DATABASE_URI']
        
        # If using S3, we need bucket configuration
        if app.config.get('STORAGE_BACKEND') == 's3':
            required.extend(['S3_BUCKET_NAME', 'S3_REGION'])
        
        missing = [key for key in required if not app.config.get(key)]
        if missing:
            raise ValueError(f"Missing required production config: {', '.join(missing)}")


class TestingConfig(BaseConfig):
    """
    Testing configuration - optimized for fast, isolated tests.
    
    Key features:
    - In-memory SQLite for speed (no disk I/O)
    - CSRF disabled for easier form testing
    - Local storage to avoid S3 calls in tests
    """
    
    TESTING = True
    DEBUG = True
    
    # Less log noise during tests
    LOG_LEVEL = 'WARNING'
    LOG_FORMAT = 'text'
    
    # In-memory database - super fast, resets between tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Local storage for tests
    STORAGE_BACKEND = 'local'
    STORAGE_PATH = '/tmp/garage-test-storage'
    
    # Disable CSRF for easier testing (don't do this in production!)
    WTF_CSRF_ENABLED = False
    
    # Don't send emails during tests
    MAIL_SUPPRESS_SEND = True


# Configuration registry - maps names to classes
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}


def get_config(config_name: str | None = None):
    """
    Get configuration class by name.
    
    Args:
        config_name: 'development', 'production', 'testing', or None
                    If None, uses FLASK_ENV environment variable
    
    Returns:
        Configuration class (not instance)
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    return config.get(config_name, config['default'])