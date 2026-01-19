# src/garage/routes/items.py
"""
Item management routes.

ROUTES:
- /box/<box_id>/item/create : Add item to box
- /item/<id>/edit : Edit item
- /item/<id>/delete : Delete item

NOTE ON DECORATORS:
- create_item uses @owns_box (we're adding to a box)
- edit_item/delete_item use @owns_item (we're modifying an item)

The @owns_item decorator passes both 'item' and 'box' to the function,
since we often need both (e.g., to redirect back to the box after editing).
"""
import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from garage.extensions import db
from garage.forms import ItemForm
from garage.models import Box, Item
from garage.utils import owns_box, owns_item

logger = logging.getLogger(__name__)

bp = Blueprint('items', __name__)


@bp.route('/box/<int:box_id>/item/create', methods=['GET', 'POST'])
@login_required
@owns_box  # Verifies user owns the box they're adding an item to
def create_item(box: Box):
    """Create a new item in a box."""
    form = ItemForm()
    
    if form.validate_on_submit():
        try:
            # Create item
            item = Item(
                name=form.name.data,
                quantity=form.quantity.data,
                category=form.category.data,
                value=float(form.value.data) if form.value.data else 0.0,
                notes=form.notes.data,
                box_id=box.id
            )
            
            db.session.add(item)
            db.session.commit()
            
            logger.info(
                "Item created",
                extra={
                    'item_id': item.id,
                    'item_name': item.name,
                    'box_id': box.id,
                    'user_id': current_user.id
                }
            )
            flash(f'Item "{item.name}" added to box!', 'success')
            return redirect(url_for('boxes.view_box', box_id=box.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(
                "Failed to create item",
                extra={'box_id': box.id, 'error': str(e)},
                exc_info=True
            )
            flash(f'Error creating item: {str(e)}', 'danger')
    
    return render_template('itemform.html', form=form, box=box, title='Add Item')


@bp.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
@owns_item  # Verifies user owns the item's box, passes both item and box
def edit_item(item: Item, box: Box):
    """Edit an existing item."""
    form = ItemForm()
    
    if form.validate_on_submit():
        try:
            # Update item fields
            item.name = form.name.data
            item.quantity = form.quantity.data
            item.category = form.category.data
            item.value = float(form.value.data) if form.value.data else 0.0
            item.notes = form.notes.data
            
            db.session.commit()
            
            logger.info(
                "Item updated",
                extra={'item_id': item.id, 'item_name': item.name, 'box_id': box.id}
            )
            flash(f'Item "{item.name}" updated successfully!', 'success')
            return redirect(url_for('boxes.view_box', box_id=box.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(
                "Failed to update item",
                extra={'item_id': item.id, 'error': str(e)},
                exc_info=True
            )
            flash(f'Error updating item: {str(e)}', 'danger')
    
    # Pre-populate form on GET request
    elif not form.is_submitted():
        form.name.data = item.name
        form.quantity.data = item.quantity
        form.category.data = item.category
        form.value.data = item.value
        form.notes.data = item.notes
    
    return render_template('itemform.html', form=form, item=item, box=box, title='Edit Item')


@bp.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
@owns_item
def delete_item(item: Item, box: Box):
    """Delete an item."""
    try:
        item_name = item.name
        item_id = item.id
        
        db.session.delete(item)
        db.session.commit()
        
        logger.info(
            "Item deleted",
            extra={
                'item_id': item_id,
                'item_name': item_name,
                'box_id': box.id,
                'user_id': current_user.id
            }
        )
        flash(f'Item "{item_name}" deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(
            "Failed to delete item",
            extra={'item_id': item.id, 'error': str(e)},
            exc_info=True
        )
        flash(f'Error deleting item: {str(e)}', 'danger')
    
    return redirect(url_for('boxes.view_box', box_id=box.id))


@bp.route('/item/<int:item_id>/move', methods=['POST'])
@login_required
@owns_item
def move_item(item: Item, box: Box):
    """Move an item to a different box."""
    new_box_id = request.form.get('new_box_id', type=int)
    
    if not new_box_id:
        flash('Please select a destination box.', 'warning')
        return redirect(url_for('boxes.view_box', box_id=box.id))
    
    # Verify user owns the destination box
    new_box = Box.query.get_or_404(new_box_id)
    if not new_box.is_owned_by(current_user.id):
        logger.warning(
            "Attempted to move item to unauthorized box",
            extra={
                'item_id': item.id,
                'source_box_id': box.id,
                'target_box_id': new_box_id,
                'user_id': current_user.id
            }
        )
        flash('You do not have permission to move items to that box.', 'danger')
        return redirect(url_for('boxes.view_box', box_id=box.id))
    
    try:
        old_box_name = box.name
        item.box_id = new_box_id
        db.session.commit()
        
        logger.info(
            "Item moved",
            extra={
                'item_id': item.id,
                'item_name': item.name,
                'from_box_id': box.id,
                'to_box_id': new_box_id,
                'user_id': current_user.id
            }
        )
        flash(f'Item "{item.name}" moved from "{old_box_name}" to "{new_box.name}".', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(
            "Failed to move item",
            extra={'item_id': item.id, 'error': str(e)},
            exc_info=True
        )
        flash(f'Error moving item: {str(e)}', 'danger')
    
    return redirect(url_for('boxes.view_box', box_id=new_box_id))


@bp.route('/item/<int:item_id>/duplicate', methods=['POST'])
@login_required
@owns_item
def duplicate_item(item: Item, box: Box):
    """Create a copy of an item in the same box."""
    try:
        # Create a new item with same properties
        new_item = Item(
            name=f"{item.name} (copy)",
            quantity=item.quantity,
            category=item.category,
            value=item.value,
            notes=item.notes,
            box_id=box.id
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        logger.info(
            "Item duplicated",
            extra={
                'original_item_id': item.id,
                'new_item_id': new_item.id,
                'box_id': box.id,
                'user_id': current_user.id
            }
        )
        flash(f'Item "{item.name}" duplicated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(
            "Failed to duplicate item",
            extra={'item_id': item.id, 'error': str(e)},
            exc_info=True
        )
        flash(f'Error duplicating item: {str(e)}', 'danger')
    
    return redirect(url_for('boxes.view_box', box_id=box.id))