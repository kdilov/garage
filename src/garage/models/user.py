# src/garage/models/user.py
"""
User model for authentication and authorization.

This model handles:
- User registration (storing username, email, hashed password)
- Authentication (password verification)
- Password reset tokens
- Admin privileges

SECURITY NOTES:
- Passwords are NEVER stored in plain text
- Reset tokens are time-limited and cryptographically signed
- Logging tracks security-relevant events (token generation, verification)
"""
from datetime import datetime, timezone
import logging
from typing import TYPE_CHECKING

from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from garage.extensions import db

# TYPE_CHECKING is False at runtime, True when type checkers run
# This avoids circular imports while still getting type hints
if TYPE_CHECKING:
    from garage.models.box import Box

logger = logging.getLogger(__name__)


class User(UserMixin, db.Model):
    """
    User account model.
    
    Inherits from:
    - UserMixin: Provides default implementations for Flask-Login
      (is_authenticated, is_active, is_anonymous, get_id)
    - db.Model: SQLAlchemy base model
    """
    __tablename__ = 'users'

    # PRIMARY KEY
    id = db.Column(db.Integer, primary_key=True)
    
    # USER IDENTITY
    # index=True creates a database index for faster lookups
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    
    # AUTHENTICATION
    # NEVER store plain passwords - always hash them
    password_hash = db.Column(db.String(255), nullable=False)
    
    # AUTHORIZATION
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    # AUDIT
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # RELATIONSHIPS
    # backref='owner' means Box instances have a .owner attribute
    # lazy='dynamic' returns a query object instead of loading all boxes
    # cascade='all, delete-orphan' deletes boxes when user is deleted
    boxes: db.Mapped[list["Box"]] = db.relationship(
        'Box',
        backref='owner',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def set_password(self, password: str) -> None:
        """
        Hash and store the user's password.
        
        Uses Werkzeug's generate_password_hash which:
        - Uses PBKDF2 by default (industry standard)
        - Automatically generates a random salt
        - Is slow by design (prevents brute force attacks)
        """
        self.password_hash = generate_password_hash(password)
        logger.debug("Password updated", extra={'user_id': self.id})

    def check_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash.
        
        Returns True if password matches, False otherwise.
        """
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self) -> str:
        """
        Generate a password reset token.
        
        The token:
        - Contains the user's email (encrypted)
        - Is signed with the app's SECRET_KEY
        - Can be verified later with verify_reset_token()
        
        Returns:
            URL-safe token string (can be used in URLs)
        """
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = serializer.dumps(self.email, salt='password-reset-salt')
        
        # Log for security audit trail
        logger.info("Password reset token generated", extra={'user_id': self.id})
        return token

    @staticmethod
    def verify_reset_token(token: str, expiry: int = 3600) -> "User | None":
        """
        Verify a password reset token and return the user if valid.
        
        Args:
            token: The token from get_reset_token()
            expiry: Maximum age of token in seconds (default: 1 hour)
        
        Returns:
            User instance if token is valid and not expired
            None if token is invalid, expired, or user not found
        """
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(
                token,
                salt='password-reset-salt',
                max_age=expiry
            )
        except Exception as e:
            # Could be: SignatureExpired, BadSignature, etc.
            logger.warning("Invalid reset token", extra={'error': str(e)})
            return None
        
        user = User.query.filter_by(email=email).first()
        if user:
            logger.info("Reset token verified", extra={'user_id': user.id})
        return user

    @property
    def box_count(self) -> int:
        """Return the number of boxes owned by this user."""
        return self.boxes.count()

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f'<User {self.username}>'