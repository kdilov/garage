# src/garage/services/storage/__init__.py
"""
Storage service for file uploads.

ARCHITECTURE: Strategy Pattern
Instead of one file with lots of if/else for different backends,
we have:
1. An abstract interface (StorageBackend) defining what storage must do
2. Concrete implementations (LocalStorageBackend, S3StorageBackend)
3. A factory that creates the right backend based on configuration

BENEFITS:
- Each backend is self-contained and testable
- Easy to add new backends (just create a new class)
- Config determines which backend is used - no code changes needed
- Backends can be swapped at runtime if needed

USAGE:
    from garage.services.storage import get_storage_backend
    
    storage = get_storage_backend()  # Returns configured backend
    url = storage.save_image(file, box_id)
    storage.delete(url)
"""
from garage.services.storage.base import StorageBackend
from garage.services.storage.factory import get_storage_backend, reset_storage_backend

__all__ = ['StorageBackend', 'get_storage_backend', 'reset_storage_backend']