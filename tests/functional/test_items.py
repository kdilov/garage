# tests/functional/test_items.py
"""
Functional tests for item management routes.
Tests CRUD operations for items.
"""


def test_create_item_page_get(test_client, init_database):
    """Test that create item page loads."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/box/1/item/create')
    assert response.status_code == 200
    assert b'Add Item' in response.data


def test_create_item(test_client, init_database):
    """Test creating a new item."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.post('/box/1/item/create', data={
        'name': 'New Test Item',
        'quantity': 3,
        'category': 'Electronics',
        'value': 49.99,
        'notes': 'Test notes'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'added to box' in response.data
    assert b'New Test Item' in response.data


def test_edit_item_page_get(test_client, init_database):
    """Test that edit item page loads."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/item/1/edit')
    assert response.status_code == 200
    assert b'Edit Item' in response.data
    assert b'Test Item' in response.data


def test_edit_item(test_client, init_database):
    """Test editing an item."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.post('/item/1/edit', data={
        'name': 'Updated Item Name',
        'quantity': 10,
        'category': 'Updated Category',
        'value': 99.99,
        'notes': 'Updated notes'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'updated successfully' in response.data
    assert b'Updated Item Name' in response.data


def test_delete_item(test_client, init_database, test_app):
    """Test deleting an item."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Create an item to delete
    test_client.post('/box/1/item/create', data={
        'name': 'Item to Delete',
        'quantity': 1
    }, follow_redirects=True)
    
    # Find the item ID
    with test_app.app_context():
        from garage.models import Item
        item = Item.query.filter_by(name='Item to Delete').first()
        item_id = item.id
    
    # Delete it
    response = test_client.post(f'/item/{item_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'deleted successfully' in response.data


def test_duplicate_item(test_client, init_database):
    """Test duplicating an item."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.post('/item/1/duplicate', follow_redirects=True)
    assert response.status_code == 200
    assert b'duplicated successfully' in response.data
    assert b'(copy)' in response.data


def test_move_item(test_client, init_database, test_app):
    """Test moving an item to another box."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Create another box to move to
    test_client.post('/box/create', data={
        'name': 'Destination Box',
        'location': 'Shed'
    }, follow_redirects=True)
    
    # Get the destination box ID
    with test_app.app_context():
        from garage.models import Box
        dest_box = Box.query.filter_by(name='Destination Box').first()
        dest_box_id = dest_box.id
    
    # Move the item
    response = test_client.post('/item/1/move', data={
        'new_box_id': dest_box_id
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'moved' in response.data


def test_create_item_requires_login(test_client):
    """Test that creating an item requires login."""
    test_client.get('/logout', follow_redirects=True)
    
    response = test_client.get('/box/1/item/create', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in' in response.data


def test_edit_item_wrong_user(test_client, init_database):
    """Test that users can't edit items they don't own."""
    # Login as other user (created in box tests)
    test_client.get('/logout', follow_redirects=True)
    
    # Register other user if not exists
    test_client.post('/register', data={
        'username': 'itemtestuser',
        'email': 'itemtest@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    test_client.post('/login', data={
        'username': 'itemtestuser',
        'password': 'password123'
    })
    
    # Try to edit testuser's item
    response = test_client.get('/item/1/edit', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' in response.data


def test_delete_item_wrong_user(test_client, init_database):
    """Test that users can't delete items they don't own."""
    test_client.get('/logout', follow_redirects=True)
    test_client.post('/login', data={
        'username': 'itemtestuser',
        'password': 'password123'
    })
    
    response = test_client.post('/item/1/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'do not have permission' in response.data


def test_move_item_to_unauthorized_box(test_client, init_database, test_app):
    """Test that users can't move items to boxes they don't own."""
    # Login as testuser
    test_client.get('/logout', follow_redirects=True)
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Create a box for itemtestuser
    with test_app.app_context():
        from garage.models import User, Box
        from garage.extensions import db
        
        other_user = User.query.filter_by(username='itemtestuser').first()
        if other_user:
            other_box = Box(
                name='Other User Box',
                location='Somewhere',
                user_id=other_user.id
            )
            db.session.add(other_box)
            db.session.commit()
            other_box_id = other_box.id
    
    # Try to move item to other user's box
    response = test_client.post('/item/1/move', data={
        'new_box_id': other_box_id
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'do not have permission' in response.data


def test_view_nonexistent_item_edit(test_client, init_database):
    """Test editing a non-existent item returns 404."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/item/9999/edit')
    assert response.status_code == 404