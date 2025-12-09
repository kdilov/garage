# tests/functional/test_admin.py
"""
Functional tests for Flask-Admin functionality.
Tests admin access control and CRUD operations.
"""
import pytest


@pytest.fixture(scope='module')
def admin_user(test_app, init_database):
    """Create an admin user for testing (module-scoped to match other fixtures)"""
    with test_app.app_context():
        from models import User
        from extensions import db
        
        # Check if admin user already exists
        existing = User.query.filter_by(username='adminuser').first()
        if not existing:
            admin = User(username='adminuser', email='admin@example.com')
            admin.set_password('adminpassword123')
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()
        
    return {'username': 'adminuser', 'password': 'adminpassword123'}


@pytest.fixture(scope='function')
def logged_in_admin(test_client, admin_user):
    """Login as admin user before test, logout after"""
    test_client.post('/login', data={
        'username': admin_user['username'],
        'password': admin_user['password']
    }, follow_redirects=True)
    yield admin_user
    test_client.get('/logout', follow_redirects=True)


@pytest.fixture(scope='function')
def logged_in_regular_user(test_client, init_database):
    """Login as regular (non-admin) user before test, logout after"""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    }, follow_redirects=True)
    yield
    test_client.get('/logout', follow_redirects=True)


# ============== Tests for unauthenticated users ==============

def test_admin_requires_login(test_client):
    """Test that admin panel redirects to login if not authenticated"""
    response = test_client.get('/admin/', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in' in response.data or b'Login' in response.data


# ============== Tests for regular (non-admin) users ==============

def test_admin_requires_admin_privileges(test_client, logged_in_regular_user):
    """Test that regular users cannot access admin panel"""
    response = test_client.get('/admin/', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' in response.data


def test_non_admin_cannot_access_users_view(test_client, logged_in_regular_user):
    """Test that non-admin users cannot access Users view"""
    response = test_client.get('/admin/admin_users/', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' in response.data


def test_non_admin_cannot_access_boxes_view(test_client, logged_in_regular_user):
    """Test that non-admin users cannot access Boxes view"""
    response = test_client.get('/admin/admin_boxes/', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' in response.data


def test_non_admin_cannot_access_items_view(test_client, logged_in_regular_user):
    """Test that non-admin users cannot access Items view"""
    response = test_client.get('/admin/admin_items/', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' in response.data


# ============== Tests for admin users ==============

def test_admin_access_granted_for_admin_user(test_client, logged_in_admin):
    """Test that admin users can access admin panel"""
    response = test_client.get('/admin/', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' not in response.data


def test_admin_users_view_accessible(test_client, logged_in_admin):
    """Test that admin can access Users view"""
    response = test_client.get('/admin/admin_users/', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' not in response.data


def test_admin_boxes_view_accessible(test_client, logged_in_admin):
    """Test that admin can access Boxes view"""
    response = test_client.get('/admin/admin_boxes/', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' not in response.data


def test_admin_items_view_accessible(test_client, logged_in_admin):
    """Test that admin can access Items view"""
    response = test_client.get('/admin/admin_items/', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' not in response.data


def test_admin_can_view_user_list(test_client, logged_in_admin):
    """Test that admin can see list of users"""
    response = test_client.get('/admin/admin_users/', follow_redirects=True)
    assert response.status_code == 200
    assert b'adminuser' in response.data or b'testuser' in response.data


def test_admin_can_view_box_list(test_client, logged_in_admin):
    """Test that admin can see list of boxes"""
    response = test_client.get('/admin/admin_boxes/', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' not in response.data


def test_admin_can_view_item_list(test_client, logged_in_admin):
    """Test that admin can see list of items"""
    response = test_client.get('/admin/admin_items/', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' not in response.data


def test_logout_removes_admin_access(test_client, admin_user):
    """Test that logging out removes admin access"""
    # Login as admin
    test_client.post('/login', data={
        'username': admin_user['username'],
        'password': admin_user['password']
    }, follow_redirects=True)
    
    # Verify admin access works
    response = test_client.get('/admin/', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' not in response.data
    
    # Logout
    test_client.get('/logout', follow_redirects=True)
    
    # Verify admin access is revoked
    response = test_client.get('/admin/', follow_redirects=True)
    assert b'Please log in' in response.data or b'Login' in response.data
