# src/garage/admin.py
"""
Flask-Admin configuration.

WHAT THIS IS:
Same as your existing admin.py, with minor improvements.

WHAT IT PROVIDES:
- Admin dashboard at /admin/
- CRUD interfaces for Users, Boxes, Items
- Protected by admin authentication

SECURITY:
- Only users with is_admin=True can access
- Unauthorized attempts are logged
- Sensitive fields (password_hash) are hidden
"""
import logging

from flask import Flask, redirect, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from garage.extensions import db
from garage.models import Box, Item, User

logger = logging.getLogger(__name__)


class SecureAdminIndexView(AdminIndexView):
    """
    Custom admin index view with authentication.
    
    The default AdminIndexView allows anyone to access /admin/.
    This subclass checks that the user is logged in AND is an admin.
    """
    
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            logger.warning(
                "Unauthorized admin access attempt",
                extra={'user_id': getattr(current_user, 'id', None)}
            )
            return redirect(url_for('auth.login'))
        return super().index()


class SecureModelView(ModelView):
    """
    Base model view with authentication.
    
    All admin model views inherit from this to get auth protection.
    """
    
    def is_accessible(self):
        """Check if current user can access this view."""
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login if not accessible."""
        return redirect(url_for('auth.login'))


class UserAdminView(SecureModelView):
    """Admin view for User model."""
    
    # Columns to show in list view
    column_list = ['id', 'username', 'email', 'is_admin', 'created_at']
    
    # Enable search on these columns
    column_searchable_list = ['username', 'email']
    
    # Enable filtering on these columns
    column_filters = ['is_admin', 'created_at']
    
    # Enable sorting on these columns
    column_sortable_list = ['id', 'username', 'email', 'is_admin', 'created_at']
    
    # Don't show password hash (security!)
    column_exclude_list = ['password_hash']
    
    # Don't allow editing password hash or boxes relationship directly
    form_excluded_columns = ['password_hash', 'boxes']
    
    # Make created_at read-only
    form_widget_args = {
        'created_at': {'disabled': True},
    }


class BoxAdminView(SecureModelView):
    """Admin view for Box model."""
    
    column_list = ['id', 'name', 'location', 'owner', 'item_count', 'created_at']
    column_searchable_list = ['name', 'location', 'description']
    column_filters = ['location', 'created_at', 'owner.username']
    column_sortable_list = ['id', 'name', 'location', 'created_at']
    
    # Custom formatters for display
    column_formatters = {
        'owner': lambda v, c, m, p: m.owner.username if m.owner else 'N/A',
        'item_count': lambda v, c, m, p: m.item_count,
    }


class ItemAdminView(SecureModelView):
    """Admin view for Item model."""
    
    column_list = ['id', 'name', 'quantity', 'category', 'value', 'box', 'created_at']
    column_searchable_list = ['name', 'category', 'notes']
    column_filters = ['category', 'created_at', 'box.name']
    column_sortable_list = ['id', 'name', 'quantity', 'category', 'value', 'created_at']
    
    column_formatters = {
        'box': lambda v, c, m, p: m.box.name if m.box else 'N/A',
    }


def init_admin(app: Flask) -> Admin:
    """
    Initialize Flask-Admin with the application.
    
    Called from create_app() during startup.
    
    Args:
        app: Flask application instance
    
    Returns:
        Admin instance
    """
    admin = Admin(
        app,
        name='Garage Inventory Admin',
        index_view=SecureAdminIndexView()
    )
    
    # Register model views
    admin.add_view(UserAdminView(User, db.session, name='Users'))
    admin.add_view(BoxAdminView(Box, db.session, name='Boxes'))
    admin.add_view(ItemAdminView(Item, db.session, name='Items'))
    
    logger.info("Flask-Admin initialized")
    
    return admin