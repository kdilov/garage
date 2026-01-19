# src/garage/routes/scanner.py
"""
QR scanner and search routes.

ROUTES:
- /scan : QR code scanner page (uses phone camera)
- /qr/<box_id> : QR code redirect endpoint
- /search : Search boxes and items

HOW QR SCANNING WORKS:
1. User opens /scan on their phone
2. Phone camera scans QR code on physical box
3. QR code contains URL like "/qr/42"
4. Browser goes to /qr/42
5. /qr/42 route checks auth and ownership
6. Redirects to /box/42 to show box contents
"""
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
    """
    Display QR code scanner page.
    
    This page uses JavaScript (html5-qrcode library) to access
    the phone's camera and scan QR codes.
    """
    logger.debug("Scanner page accessed", extra={'user_id': current_user.id})
    return render_template('scanner.html')


@bp.route('/qr/<int:box_id>')
@login_required
def scan_redirect(box_id: int):
    """
    Handle QR code scan redirect.
    
    This is the URL encoded in each box's QR code.
    When scanned, it:
    1. Verifies the user is logged in (@login_required)
    2. Verifies the user owns the box
    3. Redirects to the box detail page
    
    WHY NOT GO DIRECTLY TO /box/<id>:
    This intermediate step lets us:
    - Log QR scans separately from direct visits
    - Add scan-specific logic later (e.g., scan history)
    - Show a different message for scans vs direct visits
    """
    box = Box.query.get_or_404(box_id)
    
    # Check ownership
    if not box.is_owned_by(current_user.id):
        logger.warning(
            "QR scan for unauthorized box",
            extra={'user_id': current_user.id, 'box_id': box_id}
        )
        flash('You do not have permission to view this box.', 'danger')
        return redirect(url_for('boxes.dashboard'))
    
    # Log successful scan
    logger.info(
        "QR scan successful",
        extra={'user_id': current_user.id, 'box_id': box_id}
    )
    
    return redirect(url_for('boxes.view_box', box_id=box.id))


@bp.route('/search')
@login_required
def search():
    """
    Search boxes and items.
    
    Query parameters:
    - q: Search query string
    - type: 'all', 'boxes', or 'items'
    - category: Filter items by category
    
    Only searches the current user's data (security).
    """
    query = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    search_type = request.args.get('type', 'all')
    
    boxes_results = []
    items_results = []
    categories = []
    
    # Get user's box IDs for filtering
    user_boxes = Box.query.filter_by(user_id=current_user.id).all()
    box_ids = [box.id for box in user_boxes]
    
    if query:
        logger.info(
            "Search performed",
            extra={
                'user_id': current_user.id,
                'query': query,
                'search_type': search_type,
                'category_filter': category_filter
            }
        )
        
        # Search boxes
        if search_type in ['all', 'boxes']:
            boxes_results = Box.query.filter(
                Box.user_id == current_user.id,
                db.or_(
                    Box.name.ilike(f'%{query}%'),
                    Box.location.ilike(f'%{query}%'),
                    Box.description.ilike(f'%{query}%')
                )
            ).order_by(Box.name).all()
        
        # Search items
        if search_type in ['all', 'items'] and box_ids:
            items_query = Item.query.filter(
                Item.box_id.in_(box_ids),
                db.or_(
                    Item.name.ilike(f'%{query}%'),
                    Item.category.ilike(f'%{query}%'),
                    Item.notes.ilike(f'%{query}%')
                )
            )
            
            # Apply category filter if specified
            if category_filter:
                items_query = items_query.filter(Item.category == category_filter)
            
            items_results = items_query.order_by(Item.name).all()
    
    # Get unique categories for filter dropdown
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