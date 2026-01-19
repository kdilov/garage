# src/garage/models/item.py
"""
Item model for individual stored objects.

An Item represents a single type of object stored in a Box.
Each item tracks:
- Name and quantity
- Optional category for organization
- Optional value for insurance/inventory purposes
- Notes for additional details

DATABASE CONSTRAINTS:
We use CheckConstraints to enforce data integrity at the database level.
Even if application code has a bug, the database won't allow:
- Negative quantities
- Negative values
This is defense in depth - multiple layers of validation.
"""
from datetime import datetime, timezone

from garage.extensions import db


class Item(db.Model):
    """
    Item model representing objects stored in boxes.
    
    Tracks name, quantity, category, value, and notes for each item.
    """
    __tablename__ = 'items'

    # PRIMARY KEY
    id = db.Column(db.Integer, primary_key=True)
    
    # ITEM INFORMATION
    name = db.Column(db.String(100), nullable=False, index=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    category = db.Column(db.String(50), index=True)  # Indexed for filtering
    notes = db.Column(db.Text)
    value = db.Column(db.Float, default=0.0)  # Value per item, not total
    
    # TIMESTAMPS
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # FOREIGN KEY - which box contains this item
    box_id = db.Column(db.Integer, db.ForeignKey('boxes.id'), nullable=False)

    # DATABASE CONSTRAINTS
    # These enforce data integrity at the database level
    # Even if application code fails, bad data can't be inserted
    __table_args__ = (
        db.CheckConstraint('quantity >= 0', name='check_quantity_positive'),
        db.CheckConstraint('value >= 0', name='check_value_positive'),
    )

    def __repr__(self) -> str:
        return f'<Item {self.name} (x{self.quantity})>'

    @property
    def total_value(self) -> float:
        """
        Calculate total value (quantity * unit value).
        
        If item is "Screws" with quantity=100 and value=0.10,
        total_value returns 10.00
        """
        return (self.value or 0.0) * self.quantity

    def is_owned_by(self, user_id: int) -> bool:
        """
        Check if this item's box belongs to the given user.
        
        Items don't have direct ownership - they inherit it from their box.
        This method delegates to the parent box's ownership check.
        
        Args:
            user_id: User ID to check against
            
        Returns:
            True if the item's box belongs to that user
        """
        return self.box.is_owned_by(user_id)