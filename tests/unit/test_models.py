# tests/unit/test_models.py
"""
Unit tests for database models.
These tests verify that models work correctly in isolation.
"""
from models import User, Box, Item

def test_new_user(new_user):
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the username, email, and password fields are defined correctly
    """
    assert new_user.username == 'newuser'
    assert new_user.email == 'new@example.com'
    assert new_user.password_hash != 'newpassword123'  # Should be hashed


def test_user_password_hashing(new_user):
    """
    GIVEN a User model
    WHEN setting and checking a password
    THEN verify password is hashed and can be verified
    """
    new_user.set_password('mypassword')
    assert new_user.password_hash != 'mypassword'
    assert new_user.check_password('mypassword') is True
    assert new_user.check_password('wrongpassword') is False


def test_new_box(new_box):
    """
    GIVEN a Box model
    WHEN a new Box is created
    THEN check the fields are defined correctly
    """
    assert new_box.name == 'New Box'
    assert new_box.location == 'Shed'
    assert new_box.description == 'A new test box'
    assert new_box.user_id == 1


def test_new_item(new_item):
    """
    GIVEN an Item model
    WHEN a new Item is created
    THEN check the fields are defined correctly
    """
    assert new_item.name == 'New Item'
    assert new_item.quantity == 3
    assert new_item.category == 'Sports'
    assert new_item.value == 15.99
    assert new_item.box_id == 1


def test_user_box_relationship(test_app, init_database):
    """
    GIVEN a User with boxes
    WHEN accessing the user's boxes
    THEN verify the relationship works correctly
    """
    with test_app.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert len(user.boxes) == 1
        assert user.boxes[0].name == 'Test Box'


def test_box_item_relationship(test_app, init_database):
    """
    GIVEN a Box with items
    WHEN accessing the box's items
    THEN verify the relationship works correctly
    """
    with test_app.app_context():
        box = Box.query.filter_by(name='Test Box').first()
        assert box is not None
        assert len(box.items) == 1
        assert box.items[0].name == 'Test Item'
        assert box.item_count() == 1


def test_box_total_value(test_app, init_database):
    """
    GIVEN a Box with items
    WHEN calculating total value
    THEN verify the calculation is correct
    """
    with test_app.app_context():
        box = Box.query.filter_by(name='Test Box').first()
        assert box.total_value() == 127.50  # 5 items * £25.50
