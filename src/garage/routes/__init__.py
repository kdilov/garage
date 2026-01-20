# src/garage/routes/__init__.py
"""Route blueprints registration."""
import logging

from flask import Flask

logger = logging.getLogger(__name__)


def register_blueprints(app: Flask) -> None:
    """Register all blueprints with the Flask application."""
    from garage.routes.auth import bp as auth_bp
    from garage.routes.boxes import bp as boxes_bp
    from garage.routes.items import bp as items_bp
    from garage.routes.main import bp as main_bp
    from garage.routes.scanner import bp as scanner_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(boxes_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(scanner_bp)
    
    logger.info(
        "Blueprints registered",
        extra={'blueprints': ['main', 'auth', 'boxes', 'items', 'scanner']}
    )
