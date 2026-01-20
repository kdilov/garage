# tests/unit/test_storage.py
"""
Unit tests for storage backends.
"""
import os
import tempfile
from pathlib import Path
from io import BytesIO
from unittest.mock import MagicMock, patch

from PIL import Image


def test_local_storage_init(test_app):
    """Test local storage backend initialization."""
    with test_app.app_context():
        from garage.services.storage.local import LocalStorageBackend
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageBackend(base_path=tmpdir)
            
            # Should create subdirectories
            assert (Path(tmpdir) / 'images').exists()
            assert (Path(tmpdir) / 'qrcodes').exists()


def test_local_storage_save_qr(test_app):
    """Test saving QR code to local storage."""
    with test_app.app_context():
        from garage.services.storage.local import LocalStorageBackend
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageBackend(base_path=tmpdir)
            
            # Create a test image
            img = Image.new('RGB', (100, 100), color='white')
            
            path = storage.save_qr(img, box_id=1)
            
            assert path is not None
            assert 'box_1' in path
            assert Path(path).exists()


def test_local_storage_delete(test_app):
    """Test deleting file from local storage."""
    with test_app.app_context():
        from garage.services.storage.local import LocalStorageBackend
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageBackend(base_path=tmpdir)
            
            # Create a test image and save it
            img = Image.new('RGB', (100, 100), color='white')
            path = storage.save_qr(img, box_id=1)
            
            # Verify it exists
            assert Path(path).exists()
            
            # Delete it
            result = storage.delete(path)
            assert result is True
            assert not Path(path).exists()


def test_local_storage_delete_nonexistent(test_app):
    """Test deleting non-existent file returns False."""
    with test_app.app_context():
        from garage.services.storage.local import LocalStorageBackend
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageBackend(base_path=tmpdir)
            
            result = storage.delete('/nonexistent/file.png')
            assert result is False


def test_local_storage_exists(test_app):
    """Test checking file existence."""
    with test_app.app_context():
        from garage.services.storage.local import LocalStorageBackend
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageBackend(base_path=tmpdir)
            
            # Create a test file
            img = Image.new('RGB', (100, 100), color='white')
            path = storage.save_qr(img, box_id=1)
            
            assert storage.exists(path) is True
            assert storage.exists('/nonexistent/file.png') is False


def test_local_storage_get_url(test_app):
    """Test getting URL for local file."""
    with test_app.app_context():
        from garage.services.storage.local import LocalStorageBackend
        
        storage = LocalStorageBackend(base_path='static')
        
        # Should prepend / for relative paths
        url = storage.get_url('static/images/test.png')
        assert url == '/static/images/test.png'
        
        # Should return None for empty path
        assert storage.get_url('') is None
        assert storage.get_url(None) is None
        
        # Should return as-is for absolute URLs
        url = storage.get_url('https://example.com/image.png')
        assert url == 'https://example.com/image.png'


def test_storage_factory_local(test_app):
    """Test storage factory returns local backend in testing."""
    with test_app.app_context():
        from garage.services.storage import get_storage_backend
        from garage.services.storage.local import LocalStorageBackend
        
        storage = get_storage_backend()
        assert isinstance(storage, LocalStorageBackend)