# src/garage/routes/main.py
"""
Main/public routes.

ROUTES:
- / : Landing page (redirects to dashboard if logged in)
- /health : Health check endpoint for load balancers

WHY A SEPARATE BLUEPRINT:
The landing page and health check are public (no auth required)
and don't fit into any other category, so they get their own blueprint.
"""
import logging

from flask import Blueprint, jsonify, redirect, render_template, url_for
from flask_login import current_user

from garage.extensions import db

logger = logging.getLogger(__name__)

# Create blueprint
# The first argument is the blueprint name, used in url_for()
# e.g., url_for('main.index')
bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """
    Display the landing page.
    
    If user is already logged in, redirect them to their dashboard
    instead of showing the landing page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('boxes.dashboard'))
    
    return render_template('index.html')


@bp.route('/health')
def health():
    """
    Health check endpoint for load balancers and monitoring.
    
    USE CASE:
    - AWS ALB/ELB health checks
    - Kubernetes liveness/readiness probes
    - Uptime monitoring services (Pingdom, UptimeRobot)
    
    WHAT IT CHECKS:
    - Application is running (if you get a response, it is)
    - Database connection works
    
    RESPONSE:
    - 200 OK with {"status": "healthy"} if everything works
    - 503 Service Unavailable with {"status": "unhealthy"} if something's wrong
    """
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    
    # Check database connection
    try:
        # Simple query to verify DB connection
        db.session.execute(db.text('SELECT 1'))
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = str(e)
        logger.error("Health check failed: database", extra={'error': str(e)})
    
    # Return appropriate status code
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code