# src/garage/services/storage/factory.py
"""Storage backend factory."""
import logging
from typing import TYPE_CHECKING

from flask import current_app

from garage.services.storage.base import StorageBackend

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_storage_backends: dict[int, StorageBackend] = {}


def get_storage_backend() -> StorageBackend:
    """Get the configured storage backend (cached per app context)."""
    app_id = id(current_app._get_current_object())
    
    if app_id in _storage_backends:
        return _storage_backends[app_id]
    
    backend_type = current_app.config.get('STORAGE_BACKEND', 'local')
    
    if backend_type == 's3':
        logger.info("Creating S3 storage backend")
        
        bucket_name = current_app.config.get('S3_BUCKET_NAME')
        if not bucket_name:
            raise ValueError("S3_BUCKET_NAME is required when STORAGE_BACKEND='s3'")
        
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
        logger.info("Creating local storage backend")
        
        from garage.services.storage.local import LocalStorageBackend
        
        backend = LocalStorageBackend(
            base_path=current_app.config.get('STORAGE_PATH', 'static')
        )
    
    _storage_backends[app_id] = backend
    return backend


def reset_storage_backend() -> None:
    """Reset the cached storage backend."""
    global _storage_backends
    _storage_backends = {}
    logger.info("Storage backend cache cleared")
