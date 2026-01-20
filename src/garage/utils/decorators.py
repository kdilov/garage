# src/garage/utils/decorators.py
"""Custom decorators for route handlers."""
from functools import wraps
import logging
from typing import Callable, Any

from flask import flash, redirect, url_for
from flask_login import current_user

logger = logging.getLogger(__name__)


def owns_box(f: Callable) -> Callable:
    """Decorator that verifies the current user owns the specified box."""
    @wraps(f)
    def decorated_function(box_id: int, *args: Any, **kwargs: Any):
        from garage.models import Box
        
        box = Box.query.get_or_404(box_id)
        
        if not box.is_owned_by(current_user.id):
            logger.warning("Unauthorized box access attempt", extra={
                'user_id': current_user.id,
                'box_id': box_id,
                'box_owner_id': box.user_id
            })
            flash('You do not have permission to access this box.', 'danger')
            return redirect(url_for('boxes.dashboard'))
        
        return f(box=box, *args, **kwargs)
    
    return decorated_function


def owns_item(f: Callable) -> Callable:
    """Decorator that verifies the current user owns the specified item's box."""
    @wraps(f)
    def decorated_function(item_id: int, *args: Any, **kwargs: Any):
        from garage.models import Item
        
        item = Item.query.get_or_404(item_id)
        box = item.box
        
        if not box.is_owned_by(current_user.id):
            logger.warning("Unauthorized item access attempt", extra={
                'user_id': current_user.id,
                'item_id': item_id,
                'box_id': box.id,
                'box_owner_id': box.user_id
            })
            flash('You do not have permission to access this item.', 'danger')
            return redirect(url_for('boxes.dashboard'))
        
        return f(item=item, box=box, *args, **kwargs)
    
    return decorated_function


def admin_required(f: Callable) -> Callable:
    """Decorator that requires the current user to be an admin."""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any):
        if not current_user.is_admin:
            logger.warning("Non-admin attempted admin access", extra={'user_id': current_user.id})
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('boxes.dashboard'))
        
        return f(*args, **kwargs)
    
    return decorated_function
