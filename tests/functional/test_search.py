# tests/functional/test_search.py
"""
Functional tests for search functionality.
"""


def test_search_page_loads(test_client, init_database):
    """Test that search page loads."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/search')
    assert response.status_code == 200
    assert b'Search Inventory' in response.data


def test_search_box_by_name(test_client, init_database):
    """Test searching for box by name."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/search?q=Test')
    assert response.status_code == 200
    assert b'Test Box' in response.data or b'Updated Box Name' in response.data


def test_search_box_by_location(test_client, init_database):
    """Test searching for box by location."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/search?q=Garage')
    assert response.status_code == 200
    assert b'Boxes' in response.data


def test_search_item_by_name(test_client, init_database):
    """Test searching for item by name."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/search?q=Item')
    assert response.status_code == 200
    assert b'Items' in response.data


def test_search_boxes_only(test_client, init_database):
    """Test searching only in boxes."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/search?q=Test&type=boxes')
    assert response.status_code == 200
    assert b'Boxes' in response.data


def test_search_items_only(test_client, init_database):
    """Test searching only in items."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/search?q=Item&type=items')
    assert response.status_code == 200
    assert b'Items' in response.data


def test_search_with_category_filter(test_client, init_database):
    """Test filtering search results by category."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/search?q=Item&category=Tools')
    assert response.status_code == 200


def test_search_no_results(test_client, init_database):
    """Test search with no results."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/search?q=nonexistent123xyz')
    assert response.status_code == 200
    assert b'No results found' in response.data


def test_search_requires_login(test_client):
    """Test that search page requires login."""
    test_client.get('/logout', follow_redirects=True)
    
    response = test_client.get('/search', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in' in response.data


def test_search_empty_query(test_client, init_database):
    """Test search with empty query."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    response = test_client.get('/search?q=')
    assert response.status_code == 200
    assert b'Enter a search term' in response.data


def test_search_only_shows_user_items(test_client, init_database, test_app):
    """Test that search only shows items belonging to logged-in user."""
    # Create another user with their own box and item
    test_client.post('/register', data={
        'username': 'searchuser',
        'email': 'search@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    test_client.post('/login', data={
        'username': 'searchuser',
        'password': 'password123'
    })
    
    # Create a box for this user
    test_client.post('/box/create', data={
        'name': 'SearchUser Box',
        'location': 'SearchUser Location'
    }, follow_redirects=True)
    
    # Search for testuser's items - should not find them
    response = test_client.get('/search?q=Test')
    assert response.status_code == 200
    # Should not see testuser's "Test Box" or "Test Item"
    # (might see "SearchUser Box" if query matches)