# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError
from models import User


class RegistrationForm(FlaskForm):
    username = StringField('Username', 
                          validators=[
                              DataRequired(message='Username is required'),
                              Length(min=3, max=80, message='Username must be between 3 and 80 characters')
                          ])
    
    email = StringField('Email', 
                       validators=[
                           DataRequired(message='Email is required'),
                           Email(message='Invalid email address'),
                           Length(max=120)
                       ])
    
    password = PasswordField('Password', 
                            validators=[
                                DataRequired(message='Password is required'),
                                Length(min=8, message='Password must be at least 8 characters long')
                            ])
    
    confirm_password = PasswordField('Confirm Password',
                                    validators=[
                                        DataRequired(message='Please confirm your password'),
                                        EqualTo('password', message='Passwords must match')
                                    ])
    
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')


class LoginForm(FlaskForm):
    username = StringField('Username', 
                          validators=[DataRequired(message='Username is required')])
    
    password = PasswordField('Password', 
                            validators=[DataRequired(message='Password is required')])
    
    submit = SubmitField('Login')


class BoxForm(FlaskForm):
    name = StringField('Box Name', 
                      validators=[
                          DataRequired(message='Box name is required'),
                          Length(min=1, max=100, message='Box name must be between 1 and 100 characters')
                      ])
    
    location = StringField('Location', 
                          validators=[
                              Optional(),
                              Length(max=200, message='Location must be less than 200 characters')
                          ])
    
    description = TextAreaField('Description', 
                               validators=[Optional()])
    
    submit = SubmitField('Save Box')


class ItemForm(FlaskForm):
    name = StringField('Item Name', 
                      validators=[
                          DataRequired(message='Item name is required'),
                          Length(min=1, max=100, message='Item name must be between 1 and 100 characters')
                      ])
    
    quantity = IntegerField('Quantity', 
                           validators=[
                               DataRequired(message='Quantity is required'),
                               NumberRange(min=0, message='Quantity must be 0 or greater')
                           ],
                           default=1)
    
    category = StringField('Category', 
                          validators=[
                              Optional(),
                              Length(max=50, message='Category must be less than 50 characters')
                          ])
    
    value = FloatField('Value (£)', 
                      validators=[
                          Optional(),
                          NumberRange(min=0, message='Value must be 0 or greater')
                      ],
                      default=0.0)
    
    notes = TextAreaField('Notes', 
                         validators=[Optional()])
    
    submit = SubmitField('Save Item')


class SearchForm(FlaskForm):
    search_query = StringField('Search', 
                              validators=[
                                  DataRequired(message='Please enter a search term'),
                                  Length(min=1, max=100)
                              ])
    
    submit = SubmitField('Search')