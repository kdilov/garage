# src/garage/services/storage/base.py
"""Abstract base class for storage backends."""
from abc import ABC, abstractmethod
import logging
from typing import BinaryIO

from PIL import Image


class StorageBackend(ABC):
    """Abstract interface for file storage operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def save_image(self, file: BinaryIO, box_id: int, image_type: str = 'box') -> str | None:
        """Save an uploaded image file. Returns path/URL or None on failure."""
        pass
    
    @abstractmethod
    def save_qr(self, image: Image.Image, box_id: int) -> str | None:
        """Save a PIL Image (QR code). Returns path/URL or None on failure."""
        pass
    
    @abstractmethod
    def delete(self, file_path: str) -> bool:
        """Delete a file from storage. Returns True if successful."""
        pass
    
    @abstractmethod
    def get_url(self, file_path: str) -> str | None:
        """Get displayable URL for a file."""
        pass
    
    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """Check if a file exists in storage."""
        pass
