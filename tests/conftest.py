# tests/conftest.py
"""Pytest configuration and fixtures for the test suite."""
import os
import tempfile

import pytest

from garage import create_app
from garage.extensions import db
from garage.models import User, Box, Item


@pytest.fixture(scope='module')
def test_app():
    """Create application for testing."""
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'TESTING': True,
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='module')
def test_client(test_app):
    """Create test client."""
    return test_app.test_client()


@pytest.fixture(scope='module')
def init_database(test_app):
    """Initialize database with test data."""
    with test_app.app_context():
        # Create test user
        test_user = User(username='testuser', email='test@example.com')
        test_user.set_password('testpassword123')
        db.session.add(test_user)
        db.session.commit()
        
        # Create test box
        test_box = Box(
            name='Test Box',
            location='Garage',
            description='A test storage box',
            user_id=test_user.id
        )
        db.session.add(test_box)
        db.session.commit()
        
        # Create test item
        test_item = Item(
            name='Test Item',
            quantity=5,
            category='Tools',
            value=25.50,
            notes='A test item',
            box_id=test_box.id
        )
        db.session.add(test_item)
        db.session.commit()
        
        yield


@pytest.fixture(scope='function')
def new_user():
    """Create a new user instance (not saved to DB)."""
    user = User(username='newuser', email='new@example.com')
    user.set_password('newpassword123')
    return user


@pytest.fixture(scope='function')
def new_box():
    """Create a new box instance (not saved to DB)."""
    return Box(
        name='New Box',
        location='Shed',
        description='A new test box',
        user_id=1
    )


@pytest.fixture(scope='function')
def new_item():
    """Create a new item instance (not saved to DB)."""
    return Item(
        name='New Item',
        quantity=3,
        category='Sports',
        value=15.99,
        box_id=1
    )


@pytest.fixture(scope='function')
def logged_in_client(test_client, init_database):
    """Provide a test client that's logged in as testuser."""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    }, follow_redirects=True)
    yield test_client
    test_client.get('/logout', follow_redirects=True)


@pytest.fixture(scope='function', autouse=True)
def cleanup_qr_codes():
    """Clean up QR codes after tests."""
    yield
    qr_dir = 'static/qrcodes'
    if os.path.exists(qr_dir):
        for file in os.listdir(qr_dir):
            file_path = os.path.join(qr_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")