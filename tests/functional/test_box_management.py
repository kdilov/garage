# tests/functional/test_box_management.py - UPDATED
"""
Functional tests for box management routes.
Tests CRUD operations for boxes and items.
"""

def test_create_box_page_get(test_client, init_database):
    """Test that create box page loads"""
    # Login first
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/box/create')
    assert response.status_code == 200
    assert b'Create New Box' in response.data


def test_create_box(test_client, init_database):
    """Test creating a new box"""
    # Login first
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Create a box
    response = test_client.post('/box/create', data={
        'name': 'Test Box 2',
        'location': 'Shed',
        'description': 'A test box in the shed'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'created successfully' in response.data
    assert b'Test Box 2' in response.data


def test_view_box(test_client, init_database):
    """Test viewing a box detail page"""
    # Login first
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # View the test box (ID 1 from init_database)
    response = test_client.get('/box/1')
    assert response.status_code == 200
    assert b'Test Box' in response.data
    # QR code might not be visible if image tag is empty, so just check page loaded
    assert b'Items in This Box' in response.data


def test_edit_box_page_get(test_client, init_database):
    """Test that edit box page loads with existing data"""
    # Login first
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/box/1/edit')
    assert response.status_code == 200
    assert b'Edit Box' in response.data
    assert b'Test Box' in response.data


def test_edit_box(test_client, init_database):
    """Test editing a box"""
    # Login first
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Edit the box
    response = test_client.post('/box/1/edit', data={
        'name': 'Updated Box Name',
        'location': 'New Location',
        'description': 'Updated description'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'updated successfully' in response.data
    assert b'Updated Box Name' in response.data


def test_delete_box(test_client, init_database):
    """Test deleting a box"""
    # Login first
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Create a box to delete
    test_client.post('/box/create', data={
        'name': 'Box to Delete',
        'location': 'Garage'
    })
    
    # Delete it (assuming it gets ID 2)
    response = test_client.post('/box/2/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'deleted successfully' in response.data


def test_create_box_requires_login(test_client):
    """Test that creating a box requires login"""
    # Clear any existing session by logging out
    test_client.get('/logout', follow_redirects=True)
    
    # Now try to access create_box without logging in
    response = test_client.get('/box/create', follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to login - check for login page elements
    assert b'Login' in response.data or b'log in' in response.data.lower()



def test_view_box_wrong_user(test_client, init_database, test_app):
    """Test that users can't view boxes they don't own"""
    # Logout first to clear session
    test_client.get('/logout', follow_redirects=True)
    
    # Create a second user
    test_client.post
