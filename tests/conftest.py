# tests/conftest.py
import pytest
import os
import tempfile
from app import app as flask_app
from extensions import db
from models import User, Box, Item

@pytest.fixture(scope='module')
def test_app():
    """
    Create and configure a test Flask application instance.
    Scope='module' means this fixture runs once per test module.
    """
    # Create a temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    # Configure the app for testing
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'SECRET_KEY': 'test-secret-key'
    })
    
    # Create the database and tables
    with flask_app.app_context():
        db.create_all()
        yield flask_app  # This is where the testing happens
        db.drop_all()
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='module')
def test_client(test_app):
    """
    Create a test client for making requests to the app.
    """
    return test_app.test_client()


@pytest.fixture(scope='module')
def init_database(test_app):
    """
    Initialize the database with test data.
    """
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
        
        yield  # This is where the testing happens
        
        # Cleanup is handled by test_app fixture


@pytest.fixture(scope='function')
def new_user():
    """
    Create a new user instance (not saved to database).
    Scope='function' means a fresh user for each test.
    """
    user = User(username='newuser', email='new@example.com')
    user.set_password('newpassword123')
    return user


@pytest.fixture(scope='function')
def new_box():
    """
    Create a new box instance (not saved to database).
    """
    return Box(
        name='New Box',
        location='Shed',
        description='A new test box',
        user_id=1  # Assumes test user exists
    )


@pytest.fixture(scope='function')
def new_item():
    """
    Create a new item instance (not saved to database).
    """
    return Item(
        name='New Item',
        quantity=3,
        category='Sports',
        value=15.99,
        box_id=1  # Assumes test box exists
    )

@pytest.fixture(scope='function', autouse=True)
def cleanup_qr_codes():
    """Clean up QR code files after each test"""
    yield
    # Cleanup after test
    import shutil
    qr_dir = 'static/qrcodes'
    if os.path.exists(qr_dir):
        for file in os.listdir(qr_dir):
            file_path = os.path.join(qr_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")