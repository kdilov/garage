# storage.py
"""
Storage abstraction layer for handling files locally or via Cloudinary.
"""
import os
import uuid
from flask import current_app

# Cloudinary imports (only used in production)
try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False


def init_cloudinary(app):
    """Initialize Cloudinary with app config"""
    if not CLOUDINARY_AVAILABLE:
        return
    
    if app.config.get('USE_CLOUDINARY'):
        cloudinary.config(
            cloud_name=app.config.get('CLOUDINARY_CLOUD_NAME'),
            api_key=app.config.get('CLOUDINARY_API_KEY'),
            api_secret=app.config.get('CLOUDINARY_API_SECRET'),
            secure=True
        )


def save_image(file, box_id, image_type='box'):
    """
    Save an uploaded image file.
    Returns a path/identifier that can be used to retrieve the image.
    
    Args:
        file: FileStorage object from form upload
        box_id: ID of the box this image belongs to
        image_type: 'box' for box images, 'qr' for QR codes
    
    Returns:
        str: Path or Cloudinary public_id for the saved image
    """
    if not file:
        return None
    
    use_cloudinary = current_app.config.get('USE_CLOUDINARY', False)
    
    if use_cloudinary and CLOUDINARY_AVAILABLE:
        return _save_to_cloudinary(file, box_id, image_type)
    else:
        return _save_locally(file, box_id, image_type)


def _save_locally(file, box_id, image_type):
    """Save file to local filesystem"""
    if image_type == 'qr':
        directory = 'static/qrcodes'
        filename = f"box_{box_id}.png"
    else:
        directory = 'static/images'
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        filename = f"box_{box_id}_{uuid.uuid4().hex[:8]}.{ext}"
    
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    file.save(filepath)
    return filepath


def _save_to_cloudinary(file, box_id, image_type):
    """Save file to Cloudinary"""
    folder = 'garage-inventory/qrcodes' if image_type == 'qr' else 'garage-inventory/images'
    public_id = f"{folder}/box_{box_id}_{uuid.uuid4().hex[:8]}"
    
    result = cloudinary.uploader.upload(
        file,
        public_id=public_id,
        overwrite=True,
        resource_type='image'
    )
    
    # Return the secure URL
    return result['secure_url']


def save_qr_image(pil_image, box_id):
    """
    Save a PIL Image (QR code) to storage.
    
    Args:
        pil_image: PIL Image object
        box_id: ID of the box
    
    Returns:
        str: Path or URL to the saved QR code
    """
    use_cloudinary = current_app.config.get('USE_CLOUDINARY', False)
    
    if use_cloudinary and CLOUDINARY_AVAILABLE:
        # Convert PIL image to bytes for Cloudinary
        import io
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        folder = 'garage-inventory/qrcodes'
        public_id = f"{folder}/box_{box_id}"
        
        result = cloudinary.uploader.upload(
            buffer,
            public_id=public_id,
            overwrite=True,
            resource_type='image'
        )
        return result['secure_url']
    else:
        # Save locally
        directory = 'static/qrcodes'
        os.makedirs(directory, exist_ok=True)
        filepath = f"{directory}/box_{box_id}.png"
        pil_image.save(filepath)
        return filepath


def delete_file(file_path):
    """
    Delete a file from storage.
    
    Args:
        file_path: Local path or Cloudinary URL
    
    Returns:
        bool: True if deleted successfully
    """
    if not file_path:
        return False
    
    use_cloudinary = current_app.config.get('USE_CLOUDINARY', False)
    
    # Check if it's a Cloudinary URL
    if use_cloudinary and CLOUDINARY_AVAILABLE and 'cloudinary.com' in file_path:
        return _delete_from_cloudinary(file_path)
    else:
        return _delete_locally(file_path)


def _delete_locally(file_path):
    """Delete file from local filesystem"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"Error deleting local file: {e}")
    return False


def _delete_from_cloudinary(url):
    """Delete file from Cloudinary by URL"""
    try:
        # Extract public_id from URL
        # URL format: https://res.cloudinary.com/cloud_name/image/upload/v123/folder/filename.ext
        parts = url.split('/upload/')
        if len(parts) == 2:
            # Remove version number and extension
            path = parts[1]
            # Remove version (v123456789/)
            if path.startswith('v'):
                path = '/'.join(path.split('/')[1:])
            # Remove extension
            public_id = path.rsplit('.', 1)[0]
            
            cloudinary.uploader.destroy(public_id)
            return True
    except Exception as e:
        print(f"Error deleting from Cloudinary: {e}")
    return False


def get_file_url(file_path):
    """
    Get the URL for displaying a file.
    For local files, returns the path with leading slash.
    For Cloudinary, returns the URL as-is.
    
    Args:
        file_path: Local path or Cloudinary URL
    
    Returns:
        str: URL suitable for use in templates
    """
    if not file_path:
        return None
    
    # If it's already a full URL (Cloudinary), return as-is
    if file_path.startswith('http://') or file_path.startswith('https://'):
        return file_path
    
    # Local file - ensure it starts with /
    if not file_path.startswith('/'):
        return '/' + file_path
    return file_path