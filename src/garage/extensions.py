# src/garage/extensions.py
"""
Flask extensions initialization.

WHY THIS PATTERN EXISTS:
The "extension factory" pattern solves a chicken-and-egg problem:
1. Extensions need to be imported before routes can use them
2. But extensions need the app to be configured
3. Solution: Create extensions WITHOUT the app, then bind them later

HOW IT WORKS:
1. This file creates extension instances without an app
2. create_app() calls extension.init_app(app) to bind them
3. Routes can then import extensions from here

This avoids circular imports:
- routes/boxes.py imports db from here
- this file doesn't import anything from routes
"""
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

# Database ORM
# Used everywhere: models, routes, services
db = SQLAlchemy()

# User session management
# Handles login/logout, @login_required decorator, current_user
login_manager = LoginManager()

# Email sending
# Used by email_service.py for password reset emails
mail = Mail()