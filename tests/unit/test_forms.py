# tests/unit/test_forms.py
"""
Unit tests for Flask-WTF forms.
These tests verify form validation works correctly.
"""
from garage.forms import (
    RegistrationForm,
    LoginForm,
    BoxForm,
    ItemForm,
    ForgotPasswordForm,
    ResetPasswordForm,
)


def test_login_form_valid(test_app):
    """
    GIVEN a LoginForm
    WHEN username and password are provided
    THEN form should validate successfully
    """
    with test_app.app_context():
        form = LoginForm(data={
            'username': 'testuser',
            'password': 'testpassword'
        })
        assert form.validate() is True


def test_login_form_missing_username(test_app):
    """
    GIVEN a LoginForm
    WHEN username is missing
    THEN form should fail validation
    """
    with test_app.app_context():
        form = LoginForm(data={
            'username': '',
            'password': 'testpassword'
        })
        assert form.validate() is False
        assert 'Username is required' in form.username.errors[0]


def test_login_form_missing_password(test_app):
    """
    GIVEN a LoginForm
    WHEN password is missing
    THEN form should fail validation
    """
    with test_app.app_context():
        form = LoginForm(data={
            'username': 'testuser',
            'password': ''
        })
        assert form.validate() is False
        assert 'Password is required' in form.password.errors[0]


def test_box_form_valid(test_app):
    """
    GIVEN a BoxForm
    WHEN valid box data is provided
    THEN form should validate successfully
    """
    with test_app.app_context():
        form = BoxForm(data={
            'name': 'Valid Box Name',
            'location': 'Garage',
            'description': 'A valid box'
        })
        assert form.validate() is True


def test_box_form_missing_name(test_app):
    """
    GIVEN a BoxForm
    WHEN name field is empty
    THEN form should fail validation
    """
    with test_app.app_context():
        form = BoxForm(data={
            'name': '',
            'location': 'Garage'
        })
        assert form.validate() is False
        assert 'Box name is required' in form.name.errors[0]


def test_box_form_name_too_long(test_app):
    """
    GIVEN a BoxForm
    WHEN name exceeds max length
    THEN form should fail validation
    """
    with test_app.app_context():
        form = BoxForm(data={
            'name': 'A' * 101,  # More than 100 chars
            'location': 'Garage'
        })
        assert form.validate() is False


def test_item_form_valid(test_app):
    """
    GIVEN an ItemForm
    WHEN valid item data is provided
    THEN form should validate successfully
    """
    with test_app.app_context():
        form = ItemForm(data={
            'name': 'Valid Item',
            'quantity': 5,
            'category': 'Tools',
            'value': 19.99
        })
        assert form.validate() is True


def test_item_form_missing_name(test_app):
    """
    GIVEN an ItemForm
    WHEN name is missing
    THEN form should fail validation
    """
    with test_app.app_context():
        form = ItemForm(data={
            'name': '',
            'quantity': 5
        })
        assert form.validate() is False
        assert 'Item name is required' in form.name.errors[0]


def test_item_form_negative_quantity(test_app):
    """
    GIVEN an ItemForm
    WHEN quantity is negative
    THEN form should fail validation
    """
    with test_app.app_context():
        form = ItemForm(data={
            'name': 'Test Item',
            'quantity': -1
        })
        assert form.validate() is False


def test_item_form_zero_value(test_app):
    """
    GIVEN an ItemForm
    WHEN value is zero
    THEN form should validate successfully
    """
    with test_app.app_context():
        form = ItemForm(data={
            'name': 'Test Item',
            'quantity': 1,
            'value': 0
        })
        assert form.validate() is True


def test_item_form_default_quantity(test_app):
    """
    GIVEN an ItemForm
    WHEN quantity is not provided
    THEN it should default to 1
    """
    with test_app.app_context():
        form = ItemForm()
        assert form.quantity.data == 1


def test_forgot_password_form_valid(test_app):
    """
    GIVEN a ForgotPasswordForm
    WHEN valid email is provided
    THEN form should validate successfully
    """
    with test_app.app_context():
        form = ForgotPasswordForm(data={
            'email': 'test@example.com'
        })
        assert form.validate() is True


def test_forgot_password_form_invalid_email(test_app):
    """
    GIVEN a ForgotPasswordForm
    WHEN invalid email is provided
    THEN form should fail validation
    """
    with test_app.app_context():
        form = ForgotPasswordForm(data={
            'email': 'not-an-email'
        })
        assert form.validate() is False


def test_reset_password_form_valid(test_app):
    """
    GIVEN a ResetPasswordForm
    WHEN valid matching passwords are provided
    THEN form should validate successfully
    """
    with test_app.app_context():
        form = ResetPasswordForm(data={
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        })
        assert form.validate() is True


def test_reset_password_form_mismatch(test_app):
    """
    GIVEN a ResetPasswordForm
    WHEN passwords don't match
    THEN form should fail validation
    """
    with test_app.app_context():
        form = ResetPasswordForm(data={
            'password': 'password123',
            'confirm_password': 'different123'
        })
        assert form.validate() is False


def test_reset_password_form_too_short(test_app):
    """
    GIVEN a ResetPasswordForm
    WHEN password is too short
    THEN form should fail validation
    """
    with test_app.app_context():
        form = ResetPasswordForm(data={
            'password': 'short',
            'confirm_password': 'short'
        })
        assert form.validate() is False


def test_registration_form_password_mismatch(test_app):
    """
    GIVEN a RegistrationForm
    WHEN passwords don't match
    THEN form should fail validation
    """
    with test_app.app_context():
        form = RegistrationForm(data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password123',
            'confirm_password': 'different123'
        })
        assert form.validate() is False
        assert 'Passwords must match' in str(form.confirm_password.errors)