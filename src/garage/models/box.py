# src/garage/models/box.py
"""
Box model for storage containers.

A Box represents a physical storage container in the garage.
Each box:
- Belongs to exactly one User (owner)
- Contains zero or more Items
- Has an optional image and QR code
- Tracks its location and description

KEY DESIGN DECISION: is_owned_by() method
Instead of checking `box.user_id == current_user.id` in every route,
we have a method that encapsulates this check. Benefits:
1. Single place to change if ownership logic becomes complex
2. More readable code: `if box.is_owned_by(user_id)` vs `if box.user_id == user_id`
3. Can be easily mocked in tests
"""
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from garage.extensions import db

if TYPE_CHECKING:
    from garage.models.item import Item
    from garage.models.user import User


class Box(db.Model):
    """
    Storage box/container model.
    
    Represents a physical storage container in the garage.
    Contains items and has an associated QR code for quick access.
    """
    __tablename__ = 'boxes'

    # PRIMARY KEY
    id = db.Column(db.Integer, primary_key=True)
    
    # BOX INFORMATION
    name = db.Column(db.String(100), nullable=False, index=True)
    location = db.Column(db.String(200))  # e.g., "Garage Shelf A", "Attic"
    description = db.Column(db.Text)
    
    # FILE PATHS
    # Increased to 500 chars to accommodate S3 URLs which can be long
    qr_code_path = db.Column(db.String(500))  # Path to QR code image
    image_path = db.Column(db.String(500))    # Path to box photo
    
    # TIMESTAMPS
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    # updated_at is NEW - tracks when box was last modified
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),  # Auto-updates on change
        nullable=False
    )

    # FOREIGN KEY - which user owns this box
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # RELATIONSHIPS
    # Items in this box
    items: db.Mapped[list["Item"]] = db.relationship(
        'Item',
        backref='box',
        lazy='dynamic',
        cascade='all, delete-orphan'  # Delete items when box is deleted
    )

    def __repr__(self) -> str:
        return f'<Box {self.name}>'

    @property
    def item_count(self) -> int:
        """Return the number of distinct items in this box."""
        return self.items.count()

    @property
    def total_value(self) -> float:
        """
        Calculate total value of all items in this box.
        
        Returns sum of (item.value * item.quantity) for all items.
        """
        total = 0.0
        for item in self.items:
            if item.value:
                total += item.value * item.quantity
        return total

    @property
    def total_items(self) -> int:
        """
        Calculate total number of individual items (considering quantity).
        
        If box has "Screws x100" and "Nails x50", returns 150.
        """
        return sum(item.quantity for item in self.items)

    def is_owned_by(self, user_id: int) -> bool:
        """
        Check if this box belongs to the given user.
        
        This method exists to:
        1. Centralize ownership checking logic
        2. Make the check more readable in routes
        3. Allow for future complexity (e.g., shared boxes)
        
        Args:
            user_id: User ID to check against
            
        Returns:
            True if the box belongs to that user
        """
        return self.user_id == user_id

    def get_categories(self) -> list[str]:
        """
        Get unique categories of items in this box.
        
        Useful for filtering/display purposes.
        
        Returns:
            Sorted list of unique category names (excludes None/empty)
        """
        categories = set()
        for item in self.items:
            if item.category:
                categories.add(item.category)
        return sorted(categories)