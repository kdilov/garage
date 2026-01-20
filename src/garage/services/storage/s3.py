# src/garage/services/storage/s3.py
"""AWS S3 storage backend."""
import io
import uuid
from typing import BinaryIO
from urllib.parse import urlparse

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from PIL import Image

from garage.services.storage.base import StorageBackend


class S3StorageBackend(StorageBackend):
    """AWS S3 storage implementation."""
    
    def __init__(
        self,
        bucket_name: str,
        region: str = 'eu-west-2',
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        endpoint_url: str | None = None,
        prefix: str = 'garage-inventory'
    ):
        super().__init__()
        
        self.bucket_name = bucket_name
        self.region = region
        self.prefix = prefix
        self.endpoint_url = endpoint_url
        
        client_config = Config(
            region_name=region,
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'standard'}
        )
        
        client_kwargs = {'service_name': 's3', 'config': client_config}
        
        if access_key_id and secret_access_key:
            client_kwargs['aws_access_key_id'] = access_key_id
            client_kwargs['aws_secret_access_key'] = secret_access_key
        
        if endpoint_url:
            client_kwargs['endpoint_url'] = endpoint_url
        
        self.client = boto3.client(**client_kwargs)
        
        self.logger.info("Initialized S3 storage backend", extra={
            'storage_backend': 's3',
            'bucket': bucket_name,
            'region': region,
            'prefix': prefix
        })
    
    def _get_key(self, box_id: int, image_type: str, extension: str = 'png') -> str:
        """Generate S3 key for a file."""
        if image_type == 'qr':
            return f"{self.prefix}/qrcodes/box_{box_id}.png"
        else:
            unique_id = uuid.uuid4().hex[:8]
            return f"{self.prefix}/images/box_{box_id}_{unique_id}.{extension}"
    
    def _get_url(self, key: str) -> str:
        """Construct public URL for an S3 object."""
        if self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket_name}/{key}"
        else:
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
    
    def _extract_key_from_url(self, url: str) -> str | None:
        """Extract S3 key from a URL."""
        if not url or not url.startswith(('http://', 'https://')):
            return None
        
        parsed = urlparse(url)
        
        if self.endpoint_url:
            path_parts = parsed.path.strip('/').split('/', 1)
            if len(path_parts) == 2 and path_parts[0] == self.bucket_name:
                return path_parts[1]
        else:
            if self.bucket_name in parsed.netloc:
                return parsed.path.strip('/')
        
        return None
    
    def save_image(self, file: BinaryIO, box_id: int, image_type: str = 'box') -> str | None:
        """Save uploaded image to S3."""
        self.logger.info("Saving image to S3", extra={'box_id': box_id, 'image_type': image_type})
        
        try:
            original_name = getattr(file, 'filename', 'image.jpg')
            ext = 'jpg'
            if '.' in original_name:
                ext = original_name.rsplit('.', 1)[1].lower()
            
            key = self._get_key(box_id, image_type, ext)
            
            content_types = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp',
            }
            content_type = content_types.get(ext, 'application/octet-stream')
            
            file.seek(0)
            file_content = file.read()
            
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                ContentType=content_type,
            )
            
            url = self._get_url(key)
            self.logger.info("Image saved to S3", extra={'box_id': box_id, 'key': key, 'url': url})
            return url
            
        except ClientError as e:
            self.logger.error("Failed to save image to S3", extra={
                'box_id': box_id,
                'error': str(e),
                'error_code': e.response['Error']['Code']
            }, exc_info=True)
            return None
        except Exception as e:
            self.logger.error("Unexpected error saving image to S3", extra={
                'box_id': box_id,
                'error': str(e)
            }, exc_info=True)
            return None
    
    def save_qr(self, image: Image.Image, box_id: int) -> str | None:
        """Save PIL Image (QR code) to S3."""
        self.logger.info("Saving QR code to S3", extra={'box_id': box_id})
        
        try:
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            key = self._get_key(box_id, 'qr')
            
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=buffer.getvalue(),
                ContentType='image/png',
            )
            
            url = self._get_url(key)
            self.logger.info("QR code saved to S3", extra={'box_id': box_id, 'key': key, 'url': url})
            return url
            
        except ClientError as e:
            self.logger.error("Failed to save QR code to S3", extra={
                'box_id': box_id,
                'error': str(e),
                'error_code': e.response['Error']['Code']
            }, exc_info=True)
            return None
        except Exception as e:
            self.logger.error("Unexpected error saving QR code to S3", extra={
                'box_id': box_id,
                'error': str(e)
            }, exc_info=True)
            return None
    
    def delete(self, file_path: str) -> bool:
        """Delete file from S3."""
        if not file_path:
            return False
        
        key = self._extract_key_from_url(file_path)
        
        if not key:
            self.logger.warning("Cannot extract S3 key from path", extra={'file_path': file_path})
            return False
        
        self.logger.info("Deleting file from S3", extra={'key': key})
        
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            self.logger.info("File deleted from S3", extra={'key': key})
            return True
        except ClientError as e:
            self.logger.error("Failed to delete file from S3", extra={
                'key': key,
                'error': str(e),
                'error_code': e.response['Error']['Code']
            }, exc_info=True)
            return False
    
    def get_url(self, file_path: str) -> str | None:
        """Get displayable URL for a file."""
        if not file_path:
            return None
        
        if file_path.startswith(('http://', 'https://')):
            return file_path
        
        return self._get_url(file_path)
    
    def exists(self, file_path: str) -> bool:
        """Check if file exists in S3."""
        if not file_path:
            return False
        
        key = self._extract_key_from_url(file_path)
        if not key:
            key = file_path
        
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
