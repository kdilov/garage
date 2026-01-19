# src/garage/forms.py
"""
WTForms form definitions.

WHAT THIS IS:
Same as your existing forms.py, moved to the new location.

FORMS DEFINED:
- RegistrationForm: New user signup
- LoginForm: User login
- ForgotPasswordForm: Request password reset
- ResetPasswordForm: Set new password with token
- BoxForm: Create/edit boxes
- ItemForm: Create/edit items

VALIDATION:
WTForms handles validation automatically:
- Required fields
- Email format
- Password confirmation matching
- Length limits
- Custom validators (username/email uniqueness)
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    DecimalField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)

from garage.models import User


class RegistrationForm(FlaskForm):
    """User registration form."""
    
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required'),
            Length(min=3, max=80, message='Username must be 3-80 characters')
        ]
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address')
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required'),
            Length(min=8, message='Password must be at least 8 characters')
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password'),
            EqualTo('password', message='Passwords must match')
        ]
    )
    submit = SubmitField('Register')
    
    def validate_username(self, field):
        """Custom validator: Check if username is already taken."""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken. Please choose another.')
    
    def validate_email(self, field):
        """Custom validator: Check if email is already registered."""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered. Please use another or login.')


class LoginForm(FlaskForm):
    """User login form."""
    
    username = StringField(
        'Username',
        validators=[DataRequired(message='Username is required')]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(message='Password is required')]
    )
    submit = SubmitField('Log In')


class ForgotPasswordForm(FlaskForm):
    """Password reset request form."""
    
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address')
        ]
    )
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    """Password reset form (with token)."""
    
    password = PasswordField(
        'New Password',
        validators=[
            DataRequired(message='Password is required'),
            Length(min=8, message='Password must be at least 8 characters')
        ]
    )
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(message='Please confirm your password'),
            EqualTo('password', message='Passwords must match')
        ]
    )
    submit = SubmitField('Reset Password')


class BoxForm(FlaskForm):
    """Box creation/edit form."""
    
    name = StringField(
        'Box Name',
        validators=[
            DataRequired(message='Box name is required'),
            Length(max=100, message='Name must be less than 100 characters')
        ]
    )
    location = StringField(
        'Location',
        validators=[
            Optional(),
            Length(max=200, message='Location must be less than 200 characters')
        ]
    )
    description = TextAreaField(
        'Description',
        validators=[Optional()]
    )
    image = FileField(
        'Box Image',
        validators=[
            Optional(),
            FileAllowed(
                ['jpg', 'jpeg', 'png', 'gif', 'webp'],
                'Images only (jpg, png, gif, webp)'
            )
        ]
    )
    delete_image = BooleanField('Delete current image')
    submit = SubmitField('Save Box')


class ItemForm(FlaskForm):
    """Item creation/edit form."""
    
    name = StringField(
        'Item Name',
        validators=[
            DataRequired(message='Item name is required'),
            Length(max=100, message='Name must be less than 100 characters')
        ]
    )
    quantity = IntegerField(
        'Quantity',
        validators=[
            DataRequired(message='Quantity is required'),
            NumberRange(min=0, message='Quantity must be 0 or greater')
        ],
        default=1
    )
    category = StringField(
        'Category',
        validators=[
            Optional(),
            Length(max=50, message='Category must be less than 50 characters')
        ]
    )
    value = DecimalField(
        'Value (per item)',
        validators=[
            Optional(),
            NumberRange(min=0, message='Value must be 0 or greater')
        ],
        default=0.0,
        places=2
    )
    notes = TextAreaField(
        'Notes',
        validators=[Optional()]
    )
    submit = SubmitField('Save Item')