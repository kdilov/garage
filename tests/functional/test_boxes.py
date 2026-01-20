# tests/functional/test_boxes.py
"""
Functional tests for box management routes.
Tests CRUD operations for boxes.
"""


def test_dashboard_loads(test_client, init_database):
    """Test that dashboard loads for logged in user."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/dashboard')
    assert response.status_code == 200
    assert b'My Storage Boxes' in response.data


def test_dashboard_shows_boxes(test_client, init_database):
    """Test that dashboard shows user's boxes."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/dashboard')
    assert response.status_code == 200
    assert b'Test Box' in response.data


def test_create_box_page_get(test_client, init_database):
    """Test that create box page loads."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/box/create')
    assert response.status_code == 200
    assert b'Create New Box' in response.data


def test_create_box(test_client, init_database):
    """Test creating a new box."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.post('/box/create', data={
        'name': 'New Test Box',
        'location': 'Shed',
        'description': 'A new test box in the shed'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'created successfully' in response.data
    assert b'New Test Box' in response.data


def test_view_box(test_client, init_database):
    """Test viewing a box detail page."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/box/1')
    assert response.status_code == 200
    assert b'Test Box' in response.data
    assert b'Items in This Box' in response.data


def test_view_box_shows_items(test_client, init_database):
    """Test that box detail page shows items."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/box/1')
    assert response.status_code == 200
    assert b'Test Item' in response.data


def test_edit_box_page_get(test_client, init_database):
    """Test that edit box page loads with existing data."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/box/1/edit')
    assert response.status_code == 200
    assert b'Edit Box' in response.data
    assert b'Test Box' in response.data


def test_edit_box(test_client, init_database):
    """Test editing a box."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.post('/box/1/edit', data={
        'name': 'Updated Box Name',
        'location': 'New Location',
        'description': 'Updated description'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'updated successfully' in response.data
    assert b'Updated Box Name' in response.data


def test_delete_box(test_client, init_database, test_app):
    """Test deleting a box."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Create a box to delete
    test_client.post('/box/create', data={
        'name': 'Box to Delete',
        'location': 'Garage'
    }, follow_redirects=True)
    
    # Find the box ID
    with test_app.app_context():
        from garage.models import Box
        box = Box.query.filter_by(name='Box to Delete').first()
        box_id = box.id
    
    # Delete it
    response = test_client.post(f'/box/{box_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'deleted successfully' in response.data


def test_create_box_requires_login(test_client):
    """Test that creating a box requires login."""
    test_client.get('/logout', follow_redirects=True)
    
    response = test_client.get('/box/create', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in' in response.data


def test_view_nonexistent_box(test_client, init_database):
    """Test viewing a box that doesn't exist returns 404."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/box/9999')
    assert response.status_code == 404


def test_view_box_wrong_user(test_client, init_database, test_app):
    """Test that users can't view boxes they don't own."""
    # Logout first
    test_client.get('/logout', follow_redirects=True)
    
    # Create another user
    test_client.post('/register', data={
        'username': 'otherboxuser',
        'email': 'otherbox@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    # Login as other user
    test_client.post('/login', data={
        'username': 'otherboxuser',
        'password': 'password123'
    }, follow_redirects=True)
    
    # Try to view testuser's box
    response = test_client.get('/box/1', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' in response.data


def test_edit_box_wrong_user(test_client, init_database):
    """Test that users can't edit boxes they don't own."""
    # Login as other user (created in previous test)
    test_client.get('/logout', follow_redirects=True)
    test_client.post('/login', data={
        'username': 'otherboxuser',
        'password': 'password123'
    }, follow_redirects=True)
    
    # Try to edit testuser's box
    response = test_client.get('/box/1/edit', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' in response.data


def test_delete_box_wrong_user(test_client, init_database):
    """Test that users can't delete boxes they don't own."""
    # Login as other user
    test_client.get('/logout', follow_redirects=True)
    test_client.post('/login', data={
        'username': 'otherboxuser',
        'password': 'password123'
    }, follow_redirects=True)
    
    # Try to delete testuser's box
    response = test_client.post('/box/1/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' in response.data