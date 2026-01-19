# src/garage/__init__.py
"""
Garage Inventory Application.

This is the main entry point for the application.
It contains the create_app() factory function that creates
and configures the Flask application.

WHAT IS AN APPLICATION FACTORY:
Instead of creating the app at import time (like your current app.py),
we have a function that creates the app when called. Benefits:
1. Multiple instances possible (for testing)
2. Configuration can be passed in
3. Avoids circular imports
4. Industry standard pattern

HOW TO RUN:
    # Development
    flask --app garage:create_app run
    
    # Or with Python
    python -m garage
    
    # Production (with gunicorn)
    gunicorn "garage:create_app()"
"""
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
    """
    Application factory.
    
    Creates and configures the Flask application instance.
    
    Args:
        config_name: Configuration to use ('development', 'production', 'testing')
                    If None, uses FLASK_ENV environment variable, defaulting to 'development'
    
    Returns:
        Configured Flask application instance
    
    Example:
        app = create_app('development')
        app.run()
    """
    # Determine configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Create Flask app
    # Note: We tell Flask where to find templates and static files
    # relative to the package location
    app = Flask(
        __name__,
        template_folder='../../templates',  # Up two levels from src/garage/
        static_folder='../../static',
        instance_path=str(Path(__file__).resolve().parent.parent.parent)
    )
    
    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # Initialize logging FIRST (so everything else can use it)
    configure_logging(app)
    logger.info(
        "Creating application",
        extra={'config': config_name, 'version': __version__}
    )
    
    # Initialize Flask extensions
    _init_extensions(app)
    
    # Register route blueprints
    _register_blueprints(app)
    
    # Initialize Flask-Admin
    _init_admin(app)
    
    # Register error handlers
    _register_error_handlers(app)
    
    # Register template context processors
    _register_context_processors(app)
    
    # Run any config-specific initialization
    if hasattr(config_class, 'init_app'):
        config_class.init_app(app)
    
    logger.info("Application created successfully")
    
    return app


def _init_extensions(app: Flask) -> None:
    """
    Initialize Flask extensions.
    
    Extensions are created in extensions.py without the app,
    then bound to the app here using init_app().
    """
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'  # Redirect here when @login_required fails
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # User loader callback - tells Flask-Login how to load a user
    @login_manager.user_loader
    def load_user(user_id: str):
        from garage.models import User
        return User.query.get(int(user_id))
    
    logger.debug("Extensions initialized")


def _register_blueprints(app: Flask) -> None:
    """Register route blueprints with the app."""
    from garage.routes import register_blueprints
    register_blueprints(app)


def _init_admin(app: Flask) -> None:
    """Initialize Flask-Admin dashboard."""
    from garage.admin import init_admin
    init_admin(app)


def _register_error_handlers(app: Flask) -> None:
    """
    Register custom error handlers.
    
    These display friendly error pages instead of ugly defaults.
    """
    from flask import render_template
    
    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning("404 Not Found", extra={'error': str(error)})
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        # Rollback any failed database transaction
        db.session.rollback()
        logger.error("500 Internal Server Error", exc_info=True)
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        logger.warning("403 Forbidden")
        return render_template('errors/403.html'), 403
    
    logger.debug("Error handlers registered")


def _register_context_processors(app: Flask) -> None:
    """
    Register template context processors.
    
    These add variables/functions available in all templates.
    """
    
    @app.context_processor
    def utility_processor():
        """Add utility functions to template context."""
        from garage.services.storage import get_storage_backend
        
        def get_file_url(file_path):
            """
            Get displayable URL for a file.
            
            Use in templates like: {{ get_file_url(box.image_path) }}
            """
            if not file_path:
                return None
            storage = get_storage_backend()
            return storage.get_url(file_path)
        
        return {
            'get_file_url': get_file_url,
            'app_version': __version__,
        }
    
    logger.debug("Context processors registered")