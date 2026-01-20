# src/garage/models/user.py
"""User model for authentication and authorization."""
from datetime import datetime, timezone
import logging
from typing import TYPE_CHECKING

from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from garage.extensions import db

if TYPE_CHECKING:
    from garage.models.box import Box

logger = logging.getLogger(__name__)


class User(UserMixin, db.Model):
    """User account model."""
    
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    boxes: db.Mapped[list["Box"]] = db.relationship(
        'Box',
        backref='owner',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def set_password(self, password: str) -> None:
        """Hash and store password."""
        self.password_hash = generate_password_hash(password)
        logger.debug("Password updated", extra={'user_id': self.id})

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self) -> str:
        """Generate a password reset token."""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = serializer.dumps(self.email, salt='password-reset-salt')
        logger.info("Password reset token generated", extra={'user_id': self.id})
        return token

    @staticmethod
    def verify_reset_token(token: str, expiry: int = 3600) -> "User | None":
        """Verify reset token and return user if valid."""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(token, salt='password-reset-salt', max_age=expiry)
        except Exception as e:
            logger.warning("Invalid reset token", extra={'error': str(e)})
            return None
        
        user = User.query.filter_by(email=email).first()
        if user:
            logger.info("Reset token verified", extra={'user_id': user.id})
        return user

    @property
    def box_count(self) -> int:
        """Return number of boxes owned by this user."""
        return self.boxes.count()

    def __repr__(self) -> str:
        return f'<User {self.username}>'
