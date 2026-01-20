# src/garage/routes/auth.py
"""Authentication routes."""
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

bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        flash('You are already registered and logged in!', 'info')
        return redirect(url_for('boxes.dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info("New user registered", extra={'user_id': user.id, 'username': user.username})
        flash(f'Account created successfully for {user.username}! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        flash('You are already logged in!', 'info')
        return redirect(url_for('boxes.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user)
            logger.info("User logged in", extra={'user_id': user.id})
            flash(f'Welcome back, {user.username}!', 'success')
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('boxes.dashboard'))
        else:
            logger.warning("Failed login attempt", extra={'username': form.username.data})
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
    if current_user.is_authenticated:
        return redirect(url_for('boxes.dashboard'))
    
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            if EmailService.send_password_reset(user):
                flash('A password reset link has been sent to your email.', 'info')
            else:
                flash('Error sending email. Please try again later.', 'danger')
        else:
            logger.info("Password reset requested for unknown email", extra={'email': form.email.data})
            flash('If an account with that email exists, a reset link has been sent.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('forgotpassword.html', form=form)


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token: str):
    """Handle password reset with token."""
    if current_user.is_authenticated:
        return redirect(url_for('boxes.dashboard'))
    
    expiry = current_app.config.get('PASSWORD_RESET_EXPIRY', 3600)
    user = User.verify_reset_token(token, expiry=expiry)
    
    if user is None:
        flash('Invalid or expired reset link. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        
        logger.info("Password reset completed", extra={'user_id': user.id})
        flash('Your password has been reset successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('resetpassword.html', form=form)
