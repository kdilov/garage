# admin.py
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, flash
from extensions import db
from models import User, Box, Item


class SecureAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            flash('Please log in to access the admin panel.', 'warning')
            return redirect(url_for('login'))
        if not current_user.is_admin:
            flash('You do not have permission to access the admin panel.', 'danger')
            return redirect(url_for('dashboard'))
        return super().index()


class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access the admin panel.', 'warning')
            return redirect(url_for('login'))
        flash('You do not have permission to access the admin panel.', 'danger')
        return redirect(url_for('dashboard'))


class UserAdminView(SecureModelView):
    column_list = ['id', 'username', 'email', 'is_admin', 'created_at']
    column_searchable_list = ['username', 'email']
    column_filters = ['is_admin', 'created_at']
    form_excluded_columns = ['password_hash', 'boxes']


class BoxAdminView(SecureModelView):
    column_list = ['id', 'name', 'location', 'owner', 'created_at']
    column_searchable_list = ['name', 'location', 'description']
    column_filters = ['owner.username', 'location']
    form_excluded_columns = ['items', 'qr_code_path']


class ItemAdminView(SecureModelView):
    column_list = ['id', 'name', 'quantity', 'category', 'value', 'box', 'created_at']
    column_searchable_list = ['name', 'category', 'notes']
    column_filters = ['category', 'box.name']


def init_admin(app):
    admin = Admin(
        app,
        name='Garage Inventory Admin',
        index_view=SecureAdminIndexView(name='Dashboard')
    )
    
    admin.add_view(UserAdminView(User, db.session, name='Users', endpoint='admin_users'))
    admin.add_view(BoxAdminView(Box, db.session, name='Boxes', endpoint='admin_boxes'))
    admin.add_view(ItemAdminView(Item, db.session, name='Items', endpoint='admin_items'))
    
    return admin