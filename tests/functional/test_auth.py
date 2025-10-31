# tests/functional/test_auth.py
"""
Functional tests for authentication routes.
"""

def test_register_page_get(test_client):
    """Test that registration page loads"""
    response = test_client.get('/register')
    assert response.status_code == 200
    assert b'Create Account' in response.data
    assert b'Username' in response.data


def test_register_user(test_client):
    """Test user registration with valid data"""
    response = test_client.post('/register', data={
        'username': 'newuser123',
        'email': 'newuser@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Account created successfully' in response.data


def test_login_page_get(test_client):
    """Test that login page loads"""
    response = test_client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data


def test_login_valid_user(test_client, init_database):
    """Test login with valid credentials"""
    response = test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome back' in response.data


def test_login_invalid_password(test_client, init_database):
    """Test login with invalid password"""
    # Ensure we're not logged in first
    test_client.get('/logout', follow_redirects=True)
    
    response = test_client.post('/login', data={
        'username': 'testuser',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


def test_logout(test_client, init_database):
    """Test logout functionality"""
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
    """Test that dashboard redirects to login if not authenticated"""
    response = test_client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in' in response.data


def test_home_page_logged_out(test_client):
    """Test home page for logged out users"""
    response = test_client.get('/')
    assert response.status_code == 200
    assert b'Welcome to Your Garage Inventory System' in response.data
    assert b'Login' in response.data
    assert b'Register' in response.data


def test_home_page_logged_in(test_client, init_database):
    """Test home page for logged in users"""
    # Login first
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Visit home page
    response = test_client.get('/')
    assert response.status_code == 200
    assert b'Welcome to Your Garage Inventory System' in response.data
    assert b'Go to Dashboard' in response.data
