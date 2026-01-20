# tests/functional/test_main.py
"""
Functional tests for main/public routes.
"""


def test_home_page_get(test_client):
    """Test that home page loads with GET."""
    response = test_client.get('/')
    assert response.status_code == 200
    assert b'Garage Inventory' in response.data


def test_health_check(test_client):
    """Test health check endpoint."""
    response = test_client.get('/health')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'checks' in data
    assert data['checks']['database'] == 'ok'


def test_404_page(test_client):
    """Test 404 error page."""
    response = test_client.get('/nonexistent-page-12345')
    assert response.status_code == 404
    assert b'Page Not Found' in response.data or b'404' in response.data