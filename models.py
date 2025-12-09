# models.py
from extensions import db
from flask_login import UserMixin
from datetime import datetime, timezone  # ← ADD timezone here
from werkzeug.security import generate_password_hash, check_password_hash

# User Model - Section 4 of your report
class User(UserMixin, db.Model):
    """
    User account model for authentication and box ownership.
    UserMixin provides Flask-Login required methods: is_authenticated, is_active, is_anonymous, get_id()
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)  # ← CHANGED
    
    # Relationship: one user can have many boxes
    boxes = db.relationship('Box', backref='owner', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and store password securely using werkzeug"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


# Box Model - Section 4 of your report
class Box(db.Model):
    """
    Storage box model representing physical boxes in the garage.
    Each box belongs to a user and can contain many items.
    """
    __tablename__ = 'boxes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    qr_code_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)  # ← CHANGED
    
    # Foreign key to User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship: one box can have many items
    items = db.relationship('Item', backref='box', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Box {self.name}>'
    
    def item_count(self):
        """Helper method to get total number of items in this box"""
        return len(self.items)
    
    def total_value(self):
        """Calculate total value of all items in this box"""
        return sum(item.value * item.quantity for item in self.items)


# Item Model - Section 4 of your report
class Item(db.Model):
    """
    Item model representing individual items stored in boxes.
    Each item must belong to a box.
    """
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    category = db.Column(db.String(50))
    notes = db.Column(db.Text)
    value = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)  # ← CHANGED
    
    # Foreign key to Box
    box_id = db.Column(db.Integer, db.ForeignKey('boxes.id'), nullable=False)
    
    # Constraint: quantity must be non-negative
    __table_args__ = (
        db.CheckConstraint('quantity >= 0', name='check_quantity_positive'),
    )
    
    def __repr__(self):
        return f'<Item {self.name} (x{self.quantity})>'
