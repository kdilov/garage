# src/garage/utils/decorators.py
"""
Custom decorators for route handlers.

THE PROBLEM THESE SOLVE:
Your current app.py repeats this pattern ~10 times:

    box = Box.query.get_or_404(box_id)
    if box.user_id != current_user.id:
        flash('You do not have permission...', 'danger')
        return redirect(url_for('dashboard'))

This is:
- Repetitive (DRY violation)
- Easy to forget (security risk)
- Clutters the actual business logic

THE SOLUTION:
Decorators that handle authorization automatically:

    @bp.route('/box/<int:box_id>')
    @login_required
    @owns_box
    def view_box(box):  # <-- receives box object, not box_id!
        return render_template('boxdetail.html', box=box)

HOW DECORATORS WORK:
1. @owns_box wraps your function
2. When the route is called, @owns_box runs first
3. It fetches the box, checks ownership
4. If OK, it calls your function with the box object
5. If not OK, it redirects with an error message

DECORATOR ORDER MATTERS:
    @login_required  # Runs SECOND (checks if logged in)
    @owns_box        # Runs FIRST (checks ownership)
    
Decorators are applied bottom-up, but execute top-down.
So @login_required checks login first, then @owns_box checks ownership.
"""
from functools import wraps
import logging
from typing import Callable, Any

from flask import flash, redirect, url_for
from flask_login import current_user

logger = logging.getLogger(__name__)


def owns_box(f: Callable) -> Callable:
    """
    Decorator that verifies the current user owns the specified box.
    
    BEFORE (repeated in every route):
        @app.route('/box/<int:box_id>')
        @login_required
        def view_box(box_id):
            box = Box.query.get_or_404(box_id)
            if box.user_id != current_user.id:
                flash('You do not have permission...', 'danger')
                return redirect(url_for('dashboard'))
            # actual logic here
    
    AFTER (clean and DRY):
        @bp.route('/box/<int:box_id>')
        @login_required
        @owns_box
        def view_box(box):  # receives box object!
            # actual logic here - no permission check needed
    
    IMPORTANT: 
    - The decorated function receives 'box' object, not 'box_id'
    - Must be used AFTER @login_required (so user is authenticated)
    """
    @wraps(f)  # Preserves function name and docstring
    def decorated_function(box_id: int, *args: Any, **kwargs: Any):
        # Import here to avoid circular imports
        from garage.models import Box
        
        # Get the box (returns 404 if not found)
        box = Box.query.get_or_404(box_id)
        
        # Check ownership using the model's method
        if not box.is_owned_by(current_user.id):
            # Log the unauthorized attempt (security audit)
            logger.warning(
                "Unauthorized box access attempt",
                extra={
                    'user_id': current_user.id,
                    'box_id': box_id,
                    'box_owner_id': box.user_id
                }
            )
            flash('You do not have permission to access this box.', 'danger')
            return redirect(url_for('boxes.dashboard'))
        
        # User owns the box - call the actual function
        # Pass the box object instead of box_id
        return f(box=box, *args, **kwargs)
    
    return decorated_function


def owns_item(f: Callable) -> Callable:
    """
    Decorator that verifies the current user owns the specified item's box.
    
    Items don't have direct ownership - they belong to boxes.
    So we check if the user owns the item's parent box.
    
    USAGE:
        @bp.route('/item/<int:item_id>/edit')
        @login_required
        @owns_item
        def edit_item(item, box):  # receives both item AND box!
            return render_template('itemform.html', item=item, box=box)
    
    IMPORTANT:
    - The decorated function receives both 'item' and 'box' objects
    - Must be used AFTER @login_required
    """
    @wraps(f)
    def decorated_function(item_id: int, *args: Any, **kwargs: Any):
        from garage.models import Item
        
        # Get the item (returns 404 if not found)
        item = Item.query.get_or_404(item_id)
        box = item.box  # Get the parent box
        
        # Check if user owns the box (which owns the item)
        if not box.is_owned_by(current_user.id):
            logger.warning(
                "Unauthorized item access attempt",
                extra={
                    'user_id': current_user.id,
                    'item_id': item_id,
                    'box_id': box.id,
                    'box_owner_id': box.user_id
                }
            )
            flash('You do not have permission to access this item.', 'danger')
            return redirect(url_for('boxes.dashboard'))
        
        # User owns the item's box - call the actual function
        # Pass both item and box objects
        return f(item=item, box=box, *args, **kwargs)
    
    return decorated_function


def admin_required(f: Callable) -> Callable:
    """
    Decorator that requires the current user to be an admin.
    
    USAGE:
        @bp.route('/admin/users')
        @login_required
        @admin_required
        def admin_users():
            return render_template('admin/users.html')
    
    IMPORTANT:
    - Must be used AFTER @login_required
    - Only checks is_admin flag, doesn't grant any permissions
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any):
        if not current_user.is_admin:
            logger.warning(
                "Non-admin attempted admin access",
                extra={'user_id': current_user.id}
            )
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('boxes.dashboard'))
        
        return f(*args, **kwargs)
    
    return decorated_function