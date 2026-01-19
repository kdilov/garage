# src/garage/services/storage/factory.py
"""
Storage backend factory.

WHY A FACTORY:
- Routes don't need to know which storage backend is configured
- Change one config value, entire app uses different storage
- Easy to add new backends without changing route code
- Caches the backend instance (don't create new connection each request)

HOW TO USE:
    from garage.services.storage import get_storage_backend
    
    # In any route or service:
    storage = get_storage_backend()
    url = storage.save_image(file, box_id)

The factory checks STORAGE_BACKEND config:
- 'local' -> LocalStorageBackend
- 's3' -> S3StorageBackend
"""
import logging
from typing import TYPE_CHECKING

from flask import current_app

from garage.services.storage.base import StorageBackend

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Cache the backend instance per application context
# This avoids creating new S3 clients on every request
_storage_backends: dict[int, StorageBackend] = {}


def get_storage_backend() -> StorageBackend:
    """
    Get the configured storage backend.
    
    Uses lazy initialization and caching:
    - First call creates the backend
    - Subsequent calls return the cached instance
    - Different app contexts get different instances (for testing)
    
    Returns:
        Configured StorageBackend instance (Local or S3)
    
    Raises:
        ValueError: If S3 is configured but required settings are missing
    """
    # Use app context ID for caching
    # This ensures tests with different apps get different backends
    app_id = id(current_app._get_current_object())
    
    # Return cached backend if exists
    if app_id in _storage_backends:
        return _storage_backends[app_id]
    
    # Determine which backend to create
    backend_type = current_app.config.get('STORAGE_BACKEND', 'local')
    
    if backend_type == 's3':
        # Create S3 backend
        logger.info("Creating S3 storage backend")
        
        # Validate required config
        bucket_name = current_app.config.get('S3_BUCKET_NAME')
        if not bucket_name:
            raise ValueError(
                "S3_BUCKET_NAME is required when STORAGE_BACKEND='s3'. "
                "Set it in your environment or .env file."
            )
        
        from garage.services.storage.s3 import S3StorageBackend
        
        backend = S3StorageBackend(
            bucket_name=bucket_name,
            region=current_app.config.get('S3_REGION', 'eu-west-2'),
            access_key_id=current_app.config.get('S3_ACCESS_KEY_ID'),
            secret_access_key=current_app.config.get('S3_SECRET_ACCESS_KEY'),
            endpoint_url=current_app.config.get('S3_ENDPOINT_URL'),
            prefix=current_app.config.get('S3_PREFIX', 'garage-inventory'),
        )
    else:
        # Create local storage backend (default)
        logger.info("Creating local storage backend")
        
        from garage.services.storage.local import LocalStorageBackend
        
        backend = LocalStorageBackend(
            base_path=current_app.config.get('STORAGE_PATH', 'static')
        )
    
    # Cache and return
    _storage_backends[app_id] = backend
    return backend


def reset_storage_backend() -> None:
    """
    Reset the cached storage backend.
    
    Use this when:
    - Running tests that need different backends
    - Configuration changes at runtime (rare)
    """
    global _storage_backends
    _storage_backends = {}
    logger.info("Storage backend cache cleared")