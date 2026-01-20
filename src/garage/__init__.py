# src/garage/__init__.py
"""Garage Inventory Application - Main entry point."""
import logging
import os

from flask import Flask

from garage.config import get_config
from garage.extensions import db, login_manager, mail
from garage.logging_config import configure_logging
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

__version__ = '2.0.0'

logger = logging.getLogger(__name__)


def create_app(config_name: str | None = None) -> Flask:
    """Application factory for creating Flask app instances."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(
        __name__,
        template_folder='../../templates',
        static_folder='../../static',
        instance_path=str(Path(__file__).resolve().parent.parent.parent)
    )
    
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    configure_logging(app)
    logger.info("Creating application", extra={'config': config_name, 'version': __version__})
    
    _init_extensions(app)
    _register_blueprints(app)
    _init_admin(app)
    _register_error_handlers(app)
    _register_context_processors(app)
    
    if hasattr(config_class, 'init_app'):
        config_class.init_app(app)
    
    logger.info("Application created successfully")
    return app


def _init_extensions(app: Flask) -> None:
    """Initialize Flask extensions with the app."""
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id: str):
        from garage.models import User
        return User.query.get(int(user_id))
    
    logger.debug("Extensions initialized")


def _register_blueprints(app: Flask) -> None:
    """Register route blueprints."""
    from garage.routes import register_blueprints
    register_blueprints(app)


def _init_admin(app: Flask) -> None:
    """Initialize Flask-Admin dashboard."""
    from garage.admin import init_admin
    init_admin(app)


def _register_error_handlers(app: Flask) -> None:
    """Register custom error handlers."""
    from flask import render_template
    
    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning("404 Not Found", extra={'error': str(error)})
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        logger.error("500 Internal Server Error", exc_info=True)
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        logger.warning("403 Forbidden")
        return render_template('errors/403.html'), 403
    
    logger.debug("Error handlers registered")


def _register_context_processors(app: Flask) -> None:
    """Register template context processors."""
    
    @app.context_processor
    def utility_processor():
        from garage.services.storage import get_storage_backend
        
        def get_file_url(file_path):
            """Get displayable URL for a file path."""
            if not file_path:
                return None
            storage = get_storage_backend()
            return storage.get_url(file_path)
        
        return {
            'get_file_url': get_file_url,
            'app_version': __version__,
        }
    
    logger.debug("Context processors registered")
