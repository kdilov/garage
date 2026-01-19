# src/garage/routes/auth.py
"""
Authentication routes.

ROUTES:
- /register : New user registration
- /login : User login
- /logout : User logout
- /forgot-password : Request password reset email
- /reset-password/<token> : Reset password with token

WHAT CHANGED FROM app.py:
1. Moved to blueprint (bp instead of app)
2. Uses EmailService instead of send_password_reset_email function
3. Added logging
4. url_for uses 'auth.login' instead of 'login'
"""
import logging

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from garage.extensions import db
from garage.forms import (
    ForgotPasswordForm,
    LoginForm,
    RegistrationForm,
    ResetPasswordForm,
)
from garage.models import User
from garage.services import EmailService

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    # Already logged in? Redirect to dashboard
    if current_user.is_authenticated:
        flash('You are already registered and logged in!', 'info')
        return redirect(url_for('boxes.dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        # Save to database
        db.session.add(user)
        db.session.commit()
        
        # Log the registration
        logger.info(
            "New user registered",
            extra={'user_id': user.id, 'username': user.username}
        )
        
        flash(f'Account created successfully for {user.username}! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    # Already logged in? Redirect to dashboard
    if current_user.is_authenticated:
        flash('You are already logged in!', 'info')
        return redirect(url_for('boxes.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Find user by username
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            # Login successful
            login_user(user)
            
            logger.info("User logged in", extra={'user_id': user.id})
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect to 'next' page if provided (e.g., after @login_required redirect)
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                # Only allow relative URLs (security: prevent open redirect)
                return redirect(next_page)
            return redirect(url_for('boxes.dashboard'))
        else:
            # Login failed
            logger.warning(
                "Failed login attempt",
                extra={'username': form.username.data}
            )
            flash('Invalid username or password. Please try again.', 'danger')
    
    return render_template('login.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logger.info("User logged out", extra={'user_id': current_user.id})
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('main.index'))


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle password reset request."""
    # Already logged in? No need for password reset
    if current_user.is_authenticated:
        return redirect(url_for('boxes.dashboard'))
    
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            # User exists - send reset email
            if EmailService.send_password_reset(user):
                flash('A password reset link has been sent to your email.', 'info')
            else:
                flash('Error sending email. Please try again later.', 'danger')
        else:
            # User doesn't exist - but don't reveal this (security)
            # Show same message to prevent email enumeration attacks
            logger.info(
                "Password reset requested for unknown email",
                extra={'email': form.email.data}
            )
            flash('If an account with that email exists, a reset link has been sent.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('forgotpassword.html', form=form)


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token: str):
    """Handle password reset with token."""
    # Already logged in? No need for password reset
    if current_user.is_authenticated:
        return redirect(url_for('boxes.dashboard'))
    
    # Verify the token
    expiry = current_app.config.get('PASSWORD_RESET_EXPIRY', 3600)
    user = User.verify_reset_token(token, expiry=expiry)
    
    if user is None:
        flash('Invalid or expired reset link. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        # Update password
        user.set_password(form.password.data)
        db.session.commit()
        
        logger.info("Password reset completed", extra={'user_id': user.id})
        flash('Your password has been reset successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('resetpassword.html', form=form)