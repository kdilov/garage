# tests/functional/test_auth.py
"""
Functional tests for authentication routes.
"""


def test_register_page_get(test_client):
    """Test that registration page loads."""
    response = test_client.get('/register')
    assert response.status_code == 200
    assert b'Create Account' in response.data
    assert b'Username' in response.data


def test_register_user(test_client):
    """Test user registration with valid data."""
    response = test_client.post('/register', data={
        'username': 'newuser123',
        'email': 'newuser@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Account created successfully' in response.data


def test_register_duplicate_username(test_client, init_database):
    """Test registration with existing username fails."""
    response = test_client.post('/register', data={
        'username': 'testuser',  # Already exists
        'email': 'different@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Username already taken' in response.data


def test_register_duplicate_email(test_client, init_database):
    """Test registration with existing email fails."""
    response = test_client.post('/register', data={
        'username': 'differentuser',
        'email': 'test@example.com',  # Already exists
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Email already registered' in response.data


def test_login_page_get(test_client):
    """Test that login page loads."""
    response = test_client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data


def test_login_valid_user(test_client, init_database):
    """Test login with valid credentials."""
    response = test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome back' in response.data


def test_login_invalid_password(test_client, init_database):
    """Test login with invalid password."""
    # Ensure we're not logged in first
    test_client.get('/logout', follow_redirects=True)
    
    response = test_client.post('/login', data={
        'username': 'testuser',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


def test_login_nonexistent_user(test_client, init_database):
    """Test login with non-existent user."""
    test_client.get('/logout', follow_redirects=True)
    
    response = test_client.post('/login', data={
        'username': 'nonexistent',
        'password': 'somepassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


def test_logout(test_client, init_database):
    """Test logout functionality."""
    # First login
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Then logout
    response = test_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'logged out successfully' in response.data


def test_dashboard_requires_login(test_client):
    """Test that dashboard redirects to login if not authenticated."""
    test_client.get('/logout', follow_redirects=True)
    response = test_client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in' in response.data


def test_home_page_logged_out(test_client):
    """Test home page for logged out users."""
    test_client.get('/logout', follow_redirects=True)
    response = test_client.get('/')
    assert response.status_code == 200
    assert b'Welcome to Your Garage Inventory System' in response.data
    assert b'Login' in response.data
    assert b'Register' in response.data


def test_home_page_logged_in(test_client, init_database):
    """Test home page for logged in users redirects to dashboard."""
    # Login first
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Visit home page - should redirect to dashboard
    response = test_client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b'My Storage Boxes' in response.data or b'Dashboard' in response.data


def test_forgot_password_page_get(test_client):
    """Test that forgot password page loads."""
    test_client.get('/logout', follow_redirects=True)
    response = test_client.get('/forgot-password')
    assert response.status_code == 200
    assert b'Forgot Password' in response.data


def test_forgot_password_submit(test_client, init_database):
    """Test forgot password form submission."""
    test_client.get('/logout', follow_redirects=True)
    response = test_client.post('/forgot-password', data={
        'email': 'test@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Should show success message regardless of whether email exists
    assert b'reset link has been sent' in response.data


def test_already_logged_in_redirect_from_login(test_client, init_database):
    """Test that logged in users are redirected from login page."""
    # Login first
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Try to access login page
    response = test_client.get('/login', follow_redirects=True)
    assert response.status_code == 200
    assert b'already logged in' in response.data


def test_already_logged_in_redirect_from_register(test_client, init_database):
    """Test that logged in users are redirected from register page."""
    # Login first
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Try to access register page
    response = test_client.get('/register', follow_redirects=True)
    assert response.status_code == 200
    assert b'already registered' in response.data