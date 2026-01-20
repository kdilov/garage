# src/garage/models/item.py
"""Item model for stored objects."""
from datetime import datetime, timezone

from garage.extensions import db


class Item(db.Model):
    """Item model representing objects stored in boxes."""
    
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    category = db.Column(db.String(50), index=True)
    notes = db.Column(db.Text)
    value = db.Column(db.Float, default=0.0)
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
    box_id = db.Column(db.Integer, db.ForeignKey('boxes.id'), nullable=False)

    __table_args__ = (
        db.CheckConstraint('quantity >= 0', name='check_quantity_positive'),
        db.CheckConstraint('value >= 0', name='check_value_positive'),
    )

    def __repr__(self) -> str:
        return f'<Item {self.name} (x{self.quantity})>'

    @property
    def total_value(self) -> float:
        """Calculate total value (quantity * unit value)."""
        return (self.value or 0.0) * self.quantity

    def is_owned_by(self, user_id: int) -> bool:
        """Check if this item's box belongs to the given user."""
        return self.box.is_owned_by(user_id)
