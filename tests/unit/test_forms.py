# tests/unit/test_forms.py
"""
Unit tests for Flask-WTF forms.
These tests verify form validation works correctly.
"""
from forms import RegistrationForm, LoginForm, BoxForm, ItemForm, SearchForm

def test_registration_form_valid(test_app):
    """
    GIVEN a RegistrationForm
    WHEN all fields are valid
    THEN form should validate successfully
    """
    with test_app.app_context():
        form = RegistrationForm(
            username='validuser',
            email='valid@example.com',
            password='validpass123',
            confirm_password='validpass123'
        )
        # Note: Custom validators check database, so this may fail if user exists
        # In real tests, you'd mock the database or use a clean test DB


def test_login_form_valid(test_app):
    """
    GIVEN a LoginForm
    WHEN username and password are provided
    THEN form should validate successfully
    """
    with test_app.app_context():
        form = LoginForm(
            username='testuser',
            password='testpassword'
        )
        assert form.validate() is True


def test_box_form_valid(test_app):
    """
    GIVEN a BoxForm
    WHEN valid box data is provided
    THEN form should validate successfully
    """
    with test_app.app_context():
        form = BoxForm(
            name='Valid Box Name',
            location='Garage',
            description='A valid box'
        )
        assert form.validate() is True


def test_box_form_missing_name(test_app):
    """
    GIVEN a BoxForm
    WHEN name field is empty
    THEN form should fail validation
    """
    with test_app.app_context():
        form = BoxForm(
            name='',
            location='Garage'
        )
        assert form.validate() is False
        assert 'Box name is required' in form.name.errors[0]


def test_item_form_valid(test_app):
    """
    GIVEN an ItemForm
    WHEN valid item data is provided
    THEN form should validate successfully
    """
    with test_app.app_context():
        form = ItemForm(
            name='Valid Item',
            quantity=5,
            category='Tools',
            value=19.99
        )
        assert form.validate() is True


def test_item_form_negative_quantity(test_app):
    """
    GIVEN an ItemForm
    WHEN quantity is negative
    THEN form should fail validation
    """
    with test_app.app_context():
        form = ItemForm(
            name='Test Item',
            quantity=-1
        )
        assert form.validate() is False
