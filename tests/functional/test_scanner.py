# tests/functional/test_scanner.py
"""
Functional tests for QR scanner routes.
"""


def test_scanner_page_loads(test_client, init_database):
    """Test that scanner page loads."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/scan')
    assert response.status_code == 200
    assert b'Scan Box QR Code' in response.data


def test_scanner_requires_login(test_client):
    """Test that scanner page requires login."""
    test_client.get('/logout', follow_redirects=True)
    
    response = test_client.get('/scan', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in' in response.data


def test_qr_redirect_valid_box(test_client, init_database):
    """Test QR redirect for a valid box."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/qr/1', follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to box detail page
    assert b'Items in This Box' in response.data


def test_qr_redirect_unauthorized_box(test_client, init_database):
    """Test QR redirect for unauthorized box."""
    # Login as different user
    test_client.get('/logout', follow_redirects=True)
    
    test_client.post('/register', data={
        'username': 'qruser',
        'email': 'qr@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    test_client.post('/login', data={
        'username': 'qruser',
        'password': 'password123'
    })
    
    response = test_client.get('/qr/1', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' in response.data


def test_qr_redirect_nonexistent_box(test_client, init_database):
    """Test QR redirect for non-existent box."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/qr/9999')
    assert response.status_code == 404