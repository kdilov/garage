# tests/unit/test_services.py
"""
Unit tests for service modules.
"""
import os
from unittest.mock import patch, MagicMock

from garage.services import QRService, EmailService


def test_qr_service_generate_for_box(test_app, init_database):
    """Test QR code generation for a box."""
    with test_app.app_context():
        path = QRService.generate_for_box(1)
        # Should return a path
        assert path is not None
        assert 'box_1' in path


def test_qr_service_regenerate_for_box(test_app, init_database):
    """Test QR code regeneration."""
    with test_app.app_context():
        # First generate
        old_path = QRService.generate_for_box(1)
        
        # Then regenerate
        new_path = QRService.regenerate_for_box(1, old_path)
        assert new_path is not None


def test_email_service_password_reset_suppressed(test_app, test_client, init_database):
    """Test password reset email in development mode (suppressed)."""
    with test_app.test_request_context():
        from garage.models import User
        
        user = User.query.filter_by(username='testuser').first()
        
        # In testing config, mail should be suppressed
        result = EmailService.send_password_reset(user)
        assert result is True  # Should succeed even when suppressed