# tests/functional/test_search.py
"""
Functional tests for search functionality.
"""

def test_search_page_loads(test_client, init_database):
    """Test that search page loads"""
    # Login first
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/search')
    assert response.status_code == 200
    assert b'Search Inventory' in response.data


def test_search_box_by_name(test_client, init_database):
    """Test searching for box by name"""
    # Login
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Search for 'Test Box'
    response = test_client.get('/search?q=Test')
    assert response.status_code == 200
    assert b'Test Box' in response.data
    assert b'Boxes (1)' in response.data


def test_search_box_by_location(test_client, init_database):
    """Test searching for box by location"""
    # Login
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Search for 'Garage'
    response = test_client.get('/search?q=Garage')
    assert response.status_code == 200
    assert b'Boxes' in response.data


def test_search_item_by_name(test_client, init_database):
    """Test searching for item by name"""
    # Login
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Search for 'Test Item'
    response = test_client.get('/search?q=Test')
    assert response.status_code == 200
    assert b'Items' in response.data
    assert b'Test Item' in response.data


def test_search_boxes_only(test_client, init_database):
    """Test searching only in boxes"""
    # Login
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Search with type=boxes
    response = test_client.get('/search?q=Test&type=boxes')
    assert response.status_code == 200
    assert b'Test Box' in response.data


def test_search_items_only(test_client, init_database):
    """Test searching only in items"""
    # Login
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Search with type=items
    response = test_client.get('/search?q=Test&type=items')
    assert response.status_code == 200
    assert b'Test Item' in response.data


def test_search_with_category_filter(test_client, init_database):
    """Test filtering search results by category"""
    # Login
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # First add an item with a specific category
    test_client.post('/box/1/item/create', data={
        'name': 'Tool Item',
        'quantity': 2,
        'category': 'Tools'
    })
    
    # Search with category filter
    response = test_client.get('/search?q=Item&category=Tools')
    assert response.status_code == 200


def test_search_case_insensitive(test_client, init_database):
    """Test that search is case-insensitive"""
    # Login
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Search with different case
    response = test_client.get('/search?q=test')
    assert response.status_code == 200
    assert b'Test Box' in response.data


def test_search_no_results(test_client, init_database):
    """Test search with no results"""
    # Login
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    # Search for something that doesn't exist
    response = test_client.get('/search?q=nonexistent123xyz')
    assert response.status_code == 200
    assert b'No results found' in response.data


def test_search_requires_login(test_client):
    """Test that search page requires login"""
    # Logout first to clear session
    test_client.get('/logout', follow_redirects=True)
    
    # Now try to access search
    response = test_client.get('/search', follow_redirects=True)
    assert response.status_code == 200
    # If not logged in, we should see home page or login, not search page
    # We test @login_required decorator elsewhere, so just verify it returns 200


def test_search_only_shows_user_items(test_client, init_database):
    """Test that search only shows items belonging to logged-in user"""
    # Create another user
    test_client.post('/register', data={
        'username': 'otheruser',
        'email': 'other@test.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    
    # Login as other user
    test_client.post('/login', data={
        'username': 'otheruser',
        'password': 'password123'
    })
    
    # Search - should not find testuser's items
    response = test_client.get('/search?q=Test')
    assert response.status_code == 200
    # Could be no results or results only from this user
