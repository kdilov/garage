# src/garage/services/qr_service.py
"""QR code generation service."""
import logging

import qrcode

from garage.services.storage import get_storage_backend

logger = logging.getLogger(__name__)


class QRService:
    """Service for generating and managing QR codes."""
    
    @staticmethod
    def generate_for_box(box_id: int) -> str | None:
        """Generate a QR code for a box."""
        logger.info("Generating QR code for box", extra={'box_id': box_id})
        
        try:
            box_url = f"/qr/{box_id}"
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(box_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            storage = get_storage_backend()
            path = storage.save_qr(img, box_id)
            
            if path:
                logger.info("QR code generated successfully", extra={'box_id': box_id, 'path': path})
            else:
                logger.warning("QR code generation returned no path", extra={'box_id': box_id})
            
            return path
            
        except Exception as e:
            logger.error("Failed to generate QR code", extra={'box_id': box_id, 'error': str(e)}, exc_info=True)
            return None
    
    @staticmethod
    def regenerate_for_box(box_id: int, old_path: str | None = None) -> str | None:
        """Regenerate a QR code for a box, optionally deleting the old one."""
        logger.info("Regenerating QR code for box", extra={'box_id': box_id, 'old_path': old_path})
        
        if old_path:
            storage = get_storage_backend()
            deleted = storage.delete(old_path)
            if deleted:
                logger.info("Deleted old QR code", extra={'path': old_path})
        
        return QRService.generate_for_box(box_id)
