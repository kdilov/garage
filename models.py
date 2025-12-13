# models.py
from extensions import db
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    boxes = db.relationship('Box', backref='owner', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_reset_token(self):
        """Generate a password reset token."""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(self.email, salt='password-reset-salt')
    
    @staticmethod
    def verify_reset_token(token, expiry=3600):
        """Verify a password reset token and return the user if valid."""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(
                token,
                salt='password-reset-salt',
                max_age=expiry
            )
        except Exception:
            return None
        return User.query.filter_by(email=email).first()
    
    def __repr__(self):
        return f'<User {self.username}>'


class Box(db.Model):
    __tablename__ = 'boxes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    qr_code_path = db.Column(db.String(255))
    image_path = db.Column(db.String(255)) 
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    items = db.relationship('Item', backref='box', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Box {self.name}>'
    
    def item_count(self):
        return len(self.items)
    
    def total_value(self):
        return sum(item.value * item.quantity for item in self.items if item.value)


class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    category = db.Column(db.String(50))
    notes = db.Column(db.Text)
    value = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    box_id = db.Column(db.Integer, db.ForeignKey('boxes.id'), nullable=False)
    
    __table_args__ = (
        db.CheckConstraint('quantity >= 0', name='check_quantity_positive'),
    )
    
    def __repr__(self):
        return f'<Item {self.name} (x{self.quantity})>'