# src/garage/models/box.py
"""Box model for storage containers."""
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from garage.extensions import db

if TYPE_CHECKING:
    from garage.models.item import Item
    from garage.models.user import User


class Box(db.Model):
    """Storage box/container model."""
    
    __tablename__ = 'boxes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    qr_code_path = db.Column(db.String(500))
    image_path = db.Column(db.String(500))
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    items: db.Mapped[list["Item"]] = db.relationship(
        'Item',
        backref='box',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<Box {self.name}>'

    @property
    def item_count(self) -> int:
        """Return number of distinct items in this box."""
        return self.items.count()

    @property
    def total_value(self) -> float:
        """Calculate total value of all items."""
        total = 0.0
        for item in self.items:
            if item.value:
                total += item.value * item.quantity
        return total

    @property
    def total_items(self) -> int:
        """Calculate total number of individual items (considering quantity)."""
        return sum(item.quantity for item in self.items)

    def is_owned_by(self, user_id: int) -> bool:
        """Check if this box belongs to the given user."""
        return self.user_id == user_id

    def get_categories(self) -> list[str]:
        """Get unique categories of items in this box."""
        categories = set()
        for item in self.items:
            if item.category:
                categories.add(item.category)
        return sorted(categories)
