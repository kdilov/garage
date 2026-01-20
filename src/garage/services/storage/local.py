# src/garage/services/storage/local.py
"""Local filesystem storage backend."""
import os
import uuid
from pathlib import Path
from typing import BinaryIO

from PIL import Image

from garage.services.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage implementation."""
    
    def __init__(self, base_path: str = 'static'):
        super().__init__()
        self.base_path = Path(base_path)
        self.images_path = self.base_path / 'images'
        self.qrcodes_path = self.base_path / 'qrcodes'
        
        # Ensure directories exist
        self.images_path.mkdir(parents=True, exist_ok=True)
        self.qrcodes_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Initialized local storage backend", extra={
            'storage_backend': 'local',
            'base_path': str(self.base_path)
        })
    
    def save_image(self, file: BinaryIO, box_id: int, image_type: str = 'box') -> str | None:
        """Save uploaded image to local filesystem."""
        self.logger.info("Saving image locally", extra={'box_id': box_id, 'image_type': image_type})
        
        try:
            original_name = getattr(file, 'filename', 'image.jpg')
            ext = 'jpg'
            if '.' in original_name:
                ext = original_name.rsplit('.', 1)[1].lower()
            
            unique_id = uuid.uuid4().hex[:8]
            filename = f"box_{box_id}_{unique_id}.{ext}"
            filepath = self.images_path / filename
            
            file.seek(0)
            file.save(filepath)
            
            relative_path = str(filepath)
            self.logger.info("Image saved locally", extra={'box_id': box_id, 'path': relative_path})
            return relative_path
            
        except Exception as e:
            self.logger.error("Failed to save image locally", extra={
                'box_id': box_id,
                'error': str(e)
            }, exc_info=True)
            return None
    
    def save_qr(self, image: Image.Image, box_id: int) -> str | None:
        """Save PIL Image (QR code) to local filesystem."""
        self.logger.info("Saving QR code locally", extra={'box_id': box_id})
        
        try:
            filename = f"box_{box_id}.png"
            filepath = self.qrcodes_path / filename
            
            image.save(filepath, format='PNG')
            
            relative_path = str(filepath)
            self.logger.info("QR code saved locally", extra={'box_id': box_id, 'path': relative_path})
            return relative_path
            
        except Exception as e:
            self.logger.error("Failed to save QR code locally", extra={
                'box_id': box_id,
                'error': str(e)
            }, exc_info=True)
            return None
    
    def delete(self, file_path: str) -> bool:
        """Delete file from local filesystem."""
        if not file_path:
            return False
        
        self.logger.info("Deleting file locally", extra={'file_path': file_path})
        
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                self.logger.info("File deleted locally", extra={'path': file_path})
                return True
            else:
                self.logger.warning("File not found for deletion", extra={'path': file_path})
                return False
                
        except Exception as e:
            self.logger.error("Failed to delete file locally", extra={
                'file_path': file_path,
                'error': str(e)
            }, exc_info=True)
            return False
    
    def get_url(self, file_path: str) -> str | None:
        """Get URL for local file (prepends / for static serving)."""
        if not file_path:
            return None
        
        if file_path.startswith(('http://', 'https://')):
            return file_path
        
        if not file_path.startswith('/'):
            return f'/{file_path}'
        return file_path
    
    def exists(self, file_path: str) -> bool:
        """Check if file exists on local filesystem."""
        if not file_path:
            return False
        return Path(file_path).exists()
