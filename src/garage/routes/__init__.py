# src/garage/routes/__init__.py
"""
Route blueprints registration.

WHAT ARE BLUEPRINTS:
Blueprints are Flask's way of organizing routes into modules.
Instead of one giant file with all routes, we have:
- auth.py: Login, logout, register, password reset
- boxes.py: Box CRUD operations
- items.py: Item CRUD operations
- scanner.py: QR scanning and search
- main.py: Landing page, health check

WHY BLUEPRINTS:
1. Organization: Related routes are grouped together
2. Maintainability: Easier to find and modify specific functionality
3. Collaboration: Team members can work on different blueprints
4. Testing: Can test blueprints in isolation
5. Reusability: Blueprints can be reused in other apps

URL PREFIXES:
Blueprints can have URL prefixes. We don't use them here to keep
URLs the same as before, but you could do:
    app.register_blueprint(auth_bp, url_prefix='/auth')
Then all auth routes would be under /auth/login, /auth/register, etc.
"""
import logging

from flask import Flask

logger = logging.getLogger(__name__)


def register_blueprints(app: Flask) -> None:
    """
    Register all blueprints with the Flask application.
    
    Called from create_app() during startup.
    
    Args:
        app: Flask application instance
    """
    # Import blueprints
    from garage.routes.auth import bp as auth_bp
    from garage.routes.boxes import bp as boxes_bp
    from garage.routes.items import bp as items_bp
    from garage.routes.main import bp as main_bp
    from garage.routes.scanner import bp as scanner_bp
    
    # Register each blueprint
    app.register_blueprint(main_bp)      # Landing page, health check
    app.register_blueprint(auth_bp)      # Login, register, password reset
    app.register_blueprint(boxes_bp)     # Box CRUD
    app.register_blueprint(items_bp)     # Item CRUD
    app.register_blueprint(scanner_bp)   # QR scanning, search
    
    logger.info(
        "Blueprints registered",
        extra={'blueprints': ['main', 'auth', 'boxes', 'items', 'scanner']}
    )