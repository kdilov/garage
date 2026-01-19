# src/garage/services/qr_service.py
"""
QR code generation service.

WHAT THIS REPLACES:
The generate_qr_code() function from your app.py

KEY IMPROVEMENTS:
1. Uses the storage backend (local or S3) instead of direct file operations
2. No need to pass 'app' parameter - uses Flask's current_app
3. Proper logging instead of print()
4. Added regenerate method for updating QR codes

HOW QR CODES WORK IN THIS APP:
1. User creates a box
2. QR code is generated containing URL: /qr/{box_id}
3. QR code image is saved to storage (local or S3)
4. User prints QR code and sticks it on physical box
5. When scanned, phone opens /qr/{box_id} which redirects to box detail
"""
import logging

import qrcode

from garage.services.storage import get_storage_backend

logger = logging.getLogger(__name__)


class QRService:
    """
    Service for generating and managing QR codes.
    
    QR codes link to the /qr/<box_id> endpoint, which:
    1. Checks if user is logged in
    2. Verifies user owns the box
    3. Redirects to box detail page
    """
    
    @staticmethod
    def generate_for_box(box_id: int) -> str | None:
        """
        Generate a QR code for a box.
        
        This is extracted from your original generate_qr_code() function.
        
        Args:
            box_id: ID of the box
        
        Returns:
            Path/URL to saved QR code, or None on failure
        """
        logger.info("Generating QR code for box", extra={'box_id': box_id})
        
        try:
            # The QR code contains a relative URL
            # When scanned, the phone's browser will go to:
            # https://your-domain.com/qr/42 (for box_id=42)
            box_url = f"/qr/{box_id}"
            
            # Create QR code using the qrcode library
            qr = qrcode.QRCode(
                version=1,  # Size of QR code (1 = 21x21 modules)
                error_correction=qrcode.constants.ERROR_CORRECT_L,  # 7% error correction
                box_size=10,  # Pixels per module
                border=4,  # Border size in modules (minimum is 4)
            )
            qr.add_data(box_url)
            qr.make(fit=True)
            
            # Generate PIL Image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save using storage backend (local or S3)
            storage = get_storage_backend()
            path = storage.save_qr(img, box_id)
            
            if path:
                logger.info(
                    "QR code generated successfully",
                    extra={'box_id': box_id, 'path': path}
                )
            else:
                logger.warning(
                    "QR code generation returned no path",
                    extra={'box_id': box_id}
                )
            
            return path
            
        except Exception as e:
            logger.error(
                "Failed to generate QR code",
                extra={'box_id': box_id, 'error': str(e)},
                exc_info=True
            )
            return None
    
    @staticmethod
    def regenerate_for_box(box_id: int, old_path: str | None = None) -> str | None:
        """
        Regenerate a QR code for a box, optionally deleting the old one.
        
        Use this when:
        - QR code image was corrupted
        - User wants a fresh QR code
        - Migrating storage backends
        
        Args:
            box_id: ID of the box
            old_path: Path to old QR code to delete (optional)
        
        Returns:
            Path/URL to new QR code, or None on failure
        """
        logger.info(
            "Regenerating QR code for box",
            extra={'box_id': box_id, 'old_path': old_path}
        )
        
        # Delete old QR code if it exists
        if old_path:
            storage = get_storage_backend()
            deleted = storage.delete(old_path)
            if deleted:
                logger.info("Deleted old QR code", extra={'path': old_path})
        
        # Generate new one
        return QRService.generate_for_box(box_id)