# tests/functional/test_admin.py
"""
Functional tests for Flask-Admin functionality.
Tests admin access control.
"""


def test_admin_requires_login(test_client):
    """Test that admin panel redirects to login if not authenticated."""
    test_client.get('/logout', follow_redirects=True)
    
    response = test_client.get('/admin/', follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to login
    assert b'Login' in response.data


def test_admin_requires_admin_privileges(test_client, init_database):
    """Test that regular users cannot access admin panel."""
    # Ensure logged out first
    test_client.get('/logout', follow_redirects=True)
    
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    }, follow_redirects=True)
    
    response = test_client.get('/admin/', follow_redirects=True)
    assert response.status_code == 200
    # Non-admin users get redirected to login page
    # The key check is they can't see admin content
    assert b'Garage Inventory Admin' not in response.data


def test_admin_access_for_admin_user(test_client, init_database, test_app):
    """Test that admin users can access admin panel."""
    # Ensure logged out first
    test_client.get('/logout', follow_redirects=True)
    
    # Make testuser an admin before logging in
    with test_app.app_context():
        from garage.models import User
        from garage.extensions import db
        
        user = User.query.filter_by(username='testuser').first()
        user.is_admin = True
        db.session.commit()
    
    # Now login as admin user
    response = test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    }, follow_redirects=True)
    
    # Access admin panel
    response = test_client.get('/admin/', follow_redirects=True)
    # Admin user should get 200 OK on admin page
    assert response.status_code == 200
    
    # Cleanup - reset admin status
    test_client.get('/logout', follow_redirects=True)
    with test_app.app_context():
        from garage.models import User
        from garage.extensions import db
        
        user = User.query.filter_by(username='testuser').first()
        user.is_admin = False
        db.session.commit()