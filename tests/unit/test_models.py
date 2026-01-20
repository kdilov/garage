# tests/unit/test_models.py
"""
Unit tests for database models.
These tests verify that models work correctly in isolation.
"""
from garage.models import User, Box, Item


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


def test_user_repr(new_user):
    """Test User __repr__ method."""
    assert repr(new_user) == '<User newuser>'


def test_box_repr(new_box):
    """Test Box __repr__ method."""
    assert repr(new_box) == '<Box New Box>'


def test_item_repr(new_item):
    """Test Item __repr__ method."""
    assert repr(new_item) == '<Item New Item (x3)>'


def test_item_total_value(new_item):
    """Test Item total_value property."""
    # 3 items * £15.99 = £47.97
    assert new_item.total_value == 47.97


def test_user_box_relationship(test_app, init_database):
    """
    GIVEN a User with boxes
    WHEN accessing the user's boxes
    THEN verify the relationship works correctly
    """
    with test_app.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.box_count == 1
        boxes = list(user.boxes)
        assert len(boxes) == 1
        assert boxes[0].name == 'Test Box'


def test_box_item_relationship(test_app, init_database):
    """
    GIVEN a Box with items
    WHEN accessing the box's items
    THEN verify the relationship works correctly
    """
    with test_app.app_context():
        box = Box.query.filter_by(name='Test Box').first()
        assert box is not None
        items = list(box.items)
        assert len(items) == 1
        assert items[0].name == 'Test Item'
        assert box.item_count == 1


def test_box_total_value(test_app, init_database):
    """
    GIVEN a Box with items
    WHEN calculating total value
    THEN verify the calculation is correct
    """
    with test_app.app_context():
        box = Box.query.filter_by(name='Test Box').first()
        # 5 items * £25.50 = £127.50
        assert box.total_value == 127.50


def test_box_total_items(test_app, init_database):
    """
    GIVEN a Box with items
    WHEN calculating total items (considering quantity)
    THEN verify the calculation is correct
    """
    with test_app.app_context():
        box = Box.query.filter_by(name='Test Box').first()
        assert box.total_items == 5  # quantity of test item


def test_box_is_owned_by(test_app, init_database):
    """Test Box.is_owned_by method."""
    with test_app.app_context():
        user = User.query.filter_by(username='testuser').first()
        box = Box.query.filter_by(name='Test Box').first()
        assert box.is_owned_by(user.id) is True
        assert box.is_owned_by(9999) is False


def test_item_is_owned_by(test_app, init_database):
    """Test Item.is_owned_by method."""
    with test_app.app_context():
        user = User.query.filter_by(username='testuser').first()
        item = Item.query.filter_by(name='Test Item').first()
        assert item.is_owned_by(user.id) is True
        assert item.is_owned_by(9999) is False


def test_box_get_categories(test_app, init_database):
    """Test Box.get_categories method."""
    with test_app.app_context():
        box = Box.query.filter_by(name='Test Box').first()
        categories = box.get_categories()
        assert 'Tools' in categories


def test_user_reset_token(test_app, init_database):
    """Test password reset token generation and verification."""
    with test_app.app_context():
        user = User.query.filter_by(username='testuser').first()
        token = user.get_reset_token()
        assert token is not None
        
        # Verify valid token
        verified_user = User.verify_reset_token(token)
        assert verified_user is not None
        assert verified_user.id == user.id


def test_user_reset_token_invalid(test_app, init_database):
    """Test that invalid reset token returns None."""
    with test_app.app_context():
        result = User.verify_reset_token('invalid-token')
        assert result is None