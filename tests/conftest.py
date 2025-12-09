# tests/conftest.py
import pytest
import os
import tempfile
from app import app as flask_app
from extensions import db
from models import User, Box, Item


@pytest.fixture(scope='module')
def test_app():
    db_fd, db_path = tempfile.mkstemp()
    
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='module')
def test_client(test_app):
    return test_app.test_client()


@pytest.fixture(scope='module')
def init_database(test_app):
    with test_app.app_context():
        test_user = User(username='testuser', email='test@example.com')
        test_user.set_password('testpassword123')
        db.session.add(test_user)
        db.session.commit()
        
        test_box = Box(
            name='Test Box',
            location='Garage',
            description='A test storage box',
            user_id=test_user.id
        )
        db.session.add(test_box)
        db.session.commit()
        
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
    user = User(username='newuser', email='new@example.com')
    user.set_password('newpassword123')
    return user


@pytest.fixture(scope='function')
def new_box():
    return Box(
        name='New Box',
        location='Shed',
        description='A new test box',
        user_id=1
    )


@pytest.fixture(scope='function')
def new_item():
    return Item(
        name='New Item',
        quantity=3,
        category='Sports',
        value=15.99,
        box_id=1
    )


@pytest.fixture(scope='function', autouse=True)
def cleanup_qr_codes():
    yield
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