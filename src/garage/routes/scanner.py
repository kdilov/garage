# src/garage/routes/scanner.py
"""QR scanner and search routes."""
import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from garage.extensions import db
from garage.models import Box, Item

logger = logging.getLogger(__name__)

bp = Blueprint('scanner', __name__)


@bp.route('/scan')
@login_required
def scanner():
    """Display QR code scanner page."""
    logger.debug("Scanner page accessed", extra={'user_id': current_user.id})
    return render_template('scanner.html')


@bp.route('/qr/<int:box_id>')
@login_required
def scan_redirect(box_id: int):
    """Handle QR code scan redirect."""
    box = Box.query.get_or_404(box_id)
    
    if not box.is_owned_by(current_user.id):
        logger.warning("QR scan for unauthorized box", extra={'user_id': current_user.id, 'box_id': box_id})
        flash('You do not have permission to view this box.', 'danger')
        return redirect(url_for('boxes.dashboard'))
    
    logger.info("QR scan successful", extra={'user_id': current_user.id, 'box_id': box_id})
    return redirect(url_for('boxes.view_box', box_id=box.id))


@bp.route('/search')
@login_required
def search():
    """Search boxes and items."""
    query = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    search_type = request.args.get('type', 'all')
    
    boxes_results = []
    items_results = []
    categories = []
    
    user_boxes = Box.query.filter_by(user_id=current_user.id).all()
    box_ids = [box.id for box in user_boxes]
    
    if query:
        logger.info("Search performed", extra={
            'user_id': current_user.id,
            'query': query,
            'search_type': search_type,
            'category_filter': category_filter
        })
        
        if search_type in ['all', 'boxes']:
            boxes_results = Box.query.filter(
                Box.user_id == current_user.id,
                db.or_(
                    Box.name.ilike(f'%{query}%'),
                    Box.location.ilike(f'%{query}%'),
                    Box.description.ilike(f'%{query}%')
                )
            ).order_by(Box.name).all()
        
        if search_type in ['all', 'items'] and box_ids:
            items_query = Item.query.filter(
                Item.box_id.in_(box_ids),
                db.or_(
                    Item.name.ilike(f'%{query}%'),
                    Item.category.ilike(f'%{query}%'),
                    Item.notes.ilike(f'%{query}%')
                )
            )
            
            if category_filter:
                items_query = items_query.filter(Item.category == category_filter)
            
            items_results = items_query.order_by(Item.name).all()
    
    if box_ids:
        category_rows = db.session.query(Item.category).filter(
            Item.box_id.in_(box_ids),
            Item.category.isnot(None),
            Item.category != ''
        ).distinct().all()
        categories = sorted([row[0] for row in category_rows])
    
    return render_template(
        'search.html',
        query=query,
        boxes_results=boxes_results,
        items_results=items_results,
        categories=categories,
        category_filter=category_filter,
        search_type=search_type
    )
