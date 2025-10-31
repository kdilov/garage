# tests/unit/test_routes.py
"""
Functional tests for Flask routes.
These tests verify that routes return expected responses.
"""

def test_home_page_get(test_client):
    """Test that home page loads with GET"""
    response = test_client.get('/')
    assert response.status_code == 200
    assert b'Garage Inventory' in response.data


def test_home_page_post(test_client):
    """Test that home page accepts POST requests"""
    response = test_client.post('/')
    assert response.status_code == 200
    assert b'Garage Inventory' in response.data
