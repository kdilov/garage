# src/garage/admin.py
"""Flask-Admin configuration and views."""
import logging

from flask import Flask, redirect, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from garage.extensions import db
from garage.models import Box, Item, User

logger = logging.getLogger(__name__)


class SecureAdminIndexView(AdminIndexView):
    """Admin index view with authentication check."""
    
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
    """Base model view with authentication."""
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))


class UserAdminView(SecureModelView):
    """Admin view for User model."""
    
    column_list = ['id', 'username', 'email', 'is_admin', 'created_at']
    column_searchable_list = ['username', 'email']
    column_filters = ['is_admin', 'created_at']
    column_sortable_list = ['id', 'username', 'email', 'is_admin', 'created_at']
    column_exclude_list = ['password_hash']
    form_excluded_columns = ['password_hash', 'boxes']
    form_widget_args = {'created_at': {'disabled': True}}


class BoxAdminView(SecureModelView):
    """Admin view for Box model."""
    
    column_list = ['id', 'name', 'location', 'owner', 'item_count', 'created_at']
    column_searchable_list = ['name', 'location', 'description']
    column_filters = ['location', 'created_at', 'owner.username']
    column_sortable_list = ['id', 'name', 'location', 'created_at']
    
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
    """Initialize Flask-Admin with the application."""
    admin = Admin(
        app,
        name='Garage Inventory Admin',
        index_view=SecureAdminIndexView()
    )
    
    admin.add_view(UserAdminView(User, db.session, name='Users'))
    admin.add_view(BoxAdminView(Box, db.session, name='Boxes'))
    admin.add_view(ItemAdminView(Item, db.session, name='Items'))
    
    logger.info("Flask-Admin initialized")
    return admin
