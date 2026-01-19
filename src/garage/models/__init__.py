# src/garage/models/__init__.py
"""
Database models for the Garage Inventory application.

WHY A PACKAGE INSTEAD OF A SINGLE FILE:
- Separation of concerns: each model in its own file
- Easier to find and modify specific models
- Reduces merge conflicts when multiple people edit models
- Models can grow (add methods) without bloating one file

HOW TO USE:
    # This still works (preferred):
    from garage.models import User, Box, Item
    
    # Or import specific model:
    from garage.models.user import User
"""
from garage.models.box import Box
from garage.models.item import Item
from garage.models.user import User

__all__ = ['User', 'Box', 'Item']