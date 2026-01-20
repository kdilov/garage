# src/garage/routes/main.py
"""Main/public routes."""
import logging

from flask import Blueprint, jsonify, redirect, render_template, url_for
from flask_login import current_user

from garage.extensions import db

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Display the landing page."""
    if current_user.is_authenticated:
        return redirect(url_for('boxes.dashboard'))
    return render_template('index.html')


@bp.route('/health')
def health():
    """Health check endpoint for load balancers and monitoring."""
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    
    try:
        db.session.execute(db.text('SELECT 1'))
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = str(e)
        logger.error("Health check failed: database", extra={'error': str(e)})
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code
