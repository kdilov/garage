# src/garage/routes/boxes.py
"""
Box management routes.

ROUTES:
- /dashboard : List user's boxes
- /box/create : Create new box
- /box/<id> : View box details
- /box/<id>/edit : Edit box
- /box/<id>/delete : Delete box

KEY IMPROVEMENT: @owns_box decorator
Instead of repeating ownership checks in every route, we use @owns_box.
Compare:

BEFORE (in every route):
    box = Box.query.get_or_404(box_id)
    if box.user_id != current_user.id:
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))
    # actual code...

AFTER (clean!):
    @owns_box
    def view_box(box):  # box is passed in, already verified
        # actual code...
"""
import logging

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from garage.extensions import db
from garage.forms import BoxForm
from garage.models import Box
from garage.services import QRService
from garage.services.storage import get_storage_backend
from garage.utils import owns_box

logger = logging.getLogger(__name__)

bp = Blueprint('boxes', __name__)


@bp.route('/dashboard')
@login_required
def dashboard():
    """Display user's box list."""
    # Only get boxes belonging to current user
    boxes = Box.query.filter_by(user_id=current_user.id).order_by(Box.name).all()
    
    logger.debug(
        "Dashboard loaded",
        extra={'user_id': current_user.id, 'box_count': len(boxes)}
    )
    
    return render_template('boxlist.html', boxes=boxes)


@bp.route('/box/create', methods=['GET', 'POST'])
@login_required
def create_box():
    """Create a new box."""
    form = BoxForm()
    
    if form.validate_on_submit():
        try:
            # Create box object
            box = Box(
                name=form.name.data,
                location=form.location.data,
                description=form.description.data,
                user_id=current_user.id
            )
            
            # Add to session and flush to get the ID
            db.session.add(box)
            db.session.flush()
            
            # Generate QR code
            qr_path = QRService.generate_for_box(box.id)
            box.qr_code_path = qr_path
            
            # Handle image upload if provided
            if form.image.data:
                storage = get_storage_backend()
                image_path = storage.save_image(form.image.data, box.id, 'box')
                if image_path:
                    box.image_path = image_path
            
            # Commit all changes
            db.session.commit()
            
            logger.info(
                "Box created",
                extra={'user_id': current_user.id, 'box_id': box.id, 'box_name': box.name}
            )
            flash(f'Box "{box.name}" created successfully!', 'success')
            return redirect(url_for('boxes.view_box', box_id=box.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(
                "Failed to create box",
                extra={'user_id': current_user.id, 'error': str(e)},
                exc_info=True
            )
            flash(f'Error creating box: {str(e)}', 'danger')
    
    return render_template('boxform.html', form=form, title='Create New Box')


@bp.route('/box/<int:box_id>')
@login_required
@owns_box  # <-- This decorator checks ownership and passes 'box' to the function
def view_box(box: Box):
    """
    Display box details and items.
    
    Note: Parameter is 'box' (the object), not 'box_id'.
    The @owns_box decorator fetches the box and verifies ownership.
    """
    logger.debug("Viewing box", extra={'box_id': box.id})
    return render_template('boxdetail.html', box=box)


@bp.route('/box/<int:box_id>/edit', methods=['GET', 'POST'])
@login_required
@owns_box
def edit_box(box: Box):
    """Edit an existing box."""
    form = BoxForm()
    storage = get_storage_backend()
    
    if form.validate_on_submit():
        try:
            # Update basic fields
            box.name = form.name.data
            box.location = form.location.data
            box.description = form.description.data
            
            # Handle image deletion
            if form.delete_image.data and box.image_path:
                storage.delete(box.image_path)
                box.image_path = None
                logger.info("Box image deleted", extra={'box_id': box.id})
            
            # Handle new image upload
            elif form.image.data:
                # Delete old image first
                if box.image_path:
                    storage.delete(box.image_path)
                
                # Save new image
                image_path = storage.save_image(form.image.data, box.id, 'box')
                if image_path:
                    box.image_path = image_path
            
            db.session.commit()
            
            logger.info("Box updated", extra={'box_id': box.id, 'box_name': box.name})
            flash(f'Box "{box.name}" updated successfully!', 'success')
            return redirect(url_for('boxes.view_box', box_id=box.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(
                "Failed to update box",
                extra={'box_id': box.id, 'error': str(e)},
                exc_info=True
            )
            flash(f'Error updating box: {str(e)}', 'danger')
    
    # Pre-populate form on GET request
    elif not form.is_submitted():
        form.name.data = box.name
        form.location.data = box.location
        form.description.data = box.description
    
    return render_template('boxform.html', form=form, box=box, title='Edit Box')


@bp.route('/box/<int:box_id>/delete', methods=['POST'])
@login_required
@owns_box
def delete_box(box: Box):
    """Delete a box and all associated data."""
    try:
        box_name = box.name
        box_id = box.id
        storage = get_storage_backend()
        
        # Delete associated files from storage
        if box.image_path:
            storage.delete(box.image_path)
        if box.qr_code_path:
            storage.delete(box.qr_code_path)
        
        # Delete box (cascade deletes items automatically)
        db.session.delete(box)
        db.session.commit()
        
        logger.info(
            "Box deleted",
            extra={'box_id': box_id, 'box_name': box_name, 'user_id': current_user.id}
        )
        flash(f'Box "{box_name}" deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(
            "Failed to delete box",
            extra={'box_id': box.id, 'error': str(e)},
            exc_info=True
        )
        flash(f'Error deleting box: {str(e)}', 'danger')
    
    return redirect(url_for('boxes.dashboard'))


@bp.route('/box/<int:box_id>/regenerate-qr', methods=['POST'])
@login_required
@owns_box
def regenerate_qr(box: Box):
    """Regenerate QR code for a box."""
    try:
        old_path = box.qr_code_path
        new_path = QRService.regenerate_for_box(box.id, old_path)
        
        if new_path:
            box.qr_code_path = new_path
            db.session.commit()
            
            logger.info("QR code regenerated", extra={'box_id': box.id})
            flash('QR code regenerated successfully!', 'success')
        else:
            flash('Error regenerating QR code.', 'danger')
            
    except Exception as e:
        db.session.rollback()
        logger.error(
            "Failed to regenerate QR code",
            extra={'box_id': box.id, 'error': str(e)},
            exc_info=True
        )
        flash(f'Error regenerating QR code: {str(e)}', 'danger')
    
    return redirect(url_for('boxes.view_box', box_id=box.id))