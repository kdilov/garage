# src/garage/services/storage/s3.py
"""
AWS S3 storage backend.

USE CASE:
- Production deployments (files accessible from anywhere)
- Multiple servers (all servers can access the same files)
- Serverless (Lambda, ECS, etc.)
- High availability (S3 has 99.999999999% durability)

HOW IT WORKS:
1. Files are uploaded to an S3 bucket under a configurable prefix
2. URLs are constructed using the bucket name and region
3. Files can be deleted using the URL (key is extracted)

AWS CREDENTIALS:
Boto3 (the AWS SDK) looks for credentials in this order:
1. Explicit credentials passed to this class
2. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
3. ~/.aws/credentials file
4. IAM role (if running on AWS infrastructure)

For production on AWS, use IAM roles instead of explicit credentials.
"""
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
    """
    AWS S3 storage implementation.
    
    Stores files in an S3 bucket with configurable prefix.
    Supports custom endpoints for LocalStack/MinIO testing.
    """
    
    def __init__(
        self,
        bucket_name: str,
        region: str = 'eu-west-2',
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        endpoint_url: str | None = None,
        prefix: str = 'garage-inventory'
    ):
        """
        Initialize S3 storage backend.
        
        Args:
            bucket_name: S3 bucket name (must exist already)
            region: AWS region (eu-west-2 is London)
            access_key_id: AWS access key (optional - uses default if not provided)
            secret_access_key: AWS secret key (optional)
            endpoint_url: Custom endpoint for LocalStack/MinIO testing
            prefix: Key prefix for all uploaded files (like a folder)
        """
        super().__init__()
        
        self.bucket_name = bucket_name
        self.region = region
        self.prefix = prefix
        self.endpoint_url = endpoint_url
        
        # Configure boto3 client
        # signature_version='s3v4' is required for newer regions
        client_config = Config(
            region_name=region,
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'standard'}
        )
        
        client_kwargs = {
            'service_name': 's3',
            'config': client_config,
        }
        
        # Add explicit credentials if provided
        # If not provided, boto3 uses default credential chain
        if access_key_id and secret_access_key:
            client_kwargs['aws_access_key_id'] = access_key_id
            client_kwargs['aws_secret_access_key'] = secret_access_key
        
        # Custom endpoint for LocalStack/MinIO (local development/testing)
        if endpoint_url:
            client_kwargs['endpoint_url'] = endpoint_url
        
        self.client = boto3.client(**client_kwargs)
        
        self.logger.info(
            "Initialized S3 storage backend",
            extra={
                'storage_backend': 's3',
                'bucket': bucket_name,
                'region': region,
                'prefix': prefix,
                'custom_endpoint': bool(endpoint_url)
            }
        )
    
    def _get_key(self, box_id: int, image_type: str, extension: str = 'png') -> str:
        """
        Generate S3 key (path within bucket) for a file.
        
        S3 doesn't have real folders, but keys with slashes look like folders
        in the AWS console.
        
        Examples:
            garage-inventory/qrcodes/box_42.png
            garage-inventory/images/box_42_a1b2c3d4.jpg
        """
        if image_type == 'qr':
            return f"{self.prefix}/qrcodes/box_{box_id}.png"
        else:
            unique_id = uuid.uuid4().hex[:8]
            return f"{self.prefix}/images/box_{box_id}_{unique_id}.{extension}"
    
    def _get_url(self, key: str) -> str:
        """
        Construct public URL for an S3 object.
        
        Standard format: https://bucket.s3.region.amazonaws.com/key
        Custom endpoint: http://endpoint/bucket/key
        """
        if self.endpoint_url:
            # LocalStack/MinIO format
            return f"{self.endpoint_url}/{self.bucket_name}/{key}"
        else:
            # Standard S3 URL format
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
    
    def _extract_key_from_url(self, url: str) -> str | None:
        """
        Extract S3 key from a URL.
        
        We store full URLs in the database, but need the key to delete files.
        
        Args:
            url: Full S3 URL
            
        Returns:
            S3 key or None if not parseable
        """
        if not url:
            return None
        
        if not url.startswith(('http://', 'https://')):
            return None
        
        parsed = urlparse(url)
        
        if self.endpoint_url:
            # Custom endpoint: http://endpoint/bucket/key
            path_parts = parsed.path.strip('/').split('/', 1)
            if len(path_parts) == 2 and path_parts[0] == self.bucket_name:
                return path_parts[1]
        else:
            # Standard S3: https://bucket.s3.region.amazonaws.com/key
            if self.bucket_name in parsed.netloc:
                return parsed.path.strip('/')
        
        return None
    
    def save_image(
        self,
        file: BinaryIO,
        box_id: int,
        image_type: str = 'box'
    ) -> str | None:
        """Save uploaded image to S3."""
        self.logger.info(
            "Saving image to S3",
            extra={'box_id': box_id, 'image_type': image_type, 'bucket': self.bucket_name}
        )
        
        try:
            # Determine file extension from original filename
            original_name = getattr(file, 'filename', 'image.jpg')
            ext = 'jpg'
            if '.' in original_name:
                ext = original_name.rsplit('.', 1)[1].lower()
            
            # Generate S3 key
            key = self._get_key(box_id, image_type, ext)
            
            # Set correct content type for browser display
            content_types = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp',
            }
            content_type = content_types.get(ext, 'application/octet-stream')
            
            # Read file content
            file.seek(0)  # Ensure we're at the start
            file_content = file.read()
            
            # Upload to S3
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                ContentType=content_type,
            )
            
            url = self._get_url(key)
            
            self.logger.info(
                "Image saved to S3",
                extra={'box_id': box_id, 'key': key, 'url': url}
            )
            return url
            
        except ClientError as e:
            # AWS-specific error (permissions, bucket not found, etc.)
            self.logger.error(
                "Failed to save image to S3",
                extra={
                    'box_id': box_id,
                    'error': str(e),
                    'error_code': e.response['Error']['Code']
                },
                exc_info=True
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error saving image to S3",
                extra={'box_id': box_id, 'error': str(e)},
                exc_info=True
            )
            return None
    
    def save_qr(self, image: Image.Image, box_id: int) -> str | None:
        """Save PIL Image (QR code) to S3."""
        self.logger.info(
            "Saving QR code to S3",
            extra={'box_id': box_id, 'bucket': self.bucket_name}
        )
        
        try:
            # Convert PIL image to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Generate key
            key = self._get_key(box_id, 'qr')
            
            # Upload to S3
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=buffer.getvalue(),
                ContentType='image/png',
            )
            
            url = self._get_url(key)
            
            self.logger.info(
                "QR code saved to S3",
                extra={'box_id': box_id, 'key': key, 'url': url}
            )
            return url
            
        except ClientError as e:
            self.logger.error(
                "Failed to save QR code to S3",
                extra={
                    'box_id': box_id,
                    'error': str(e),
                    'error_code': e.response['Error']['Code']
                },
                exc_info=True
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error saving QR code to S3",
                extra={'box_id': box_id, 'error': str(e)},
                exc_info=True
            )
            return None
    
    def delete(self, file_path: str) -> bool:
        """Delete file from S3."""
        if not file_path:
            return False
        
        # Extract key from URL
        key = self._extract_key_from_url(file_path)
        
        if not key:
            self.logger.warning(
                "Cannot extract S3 key from path",
                extra={'file_path': file_path}
            )
            return False
        
        self.logger.info(
            "Deleting file from S3",
            extra={'key': key, 'bucket': self.bucket_name}
        )
        
        try:
            # S3 delete_object doesn't error if file doesn't exist
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            self.logger.info("File deleted from S3", extra={'key': key})
            return True
            
        except ClientError as e:
            self.logger.error(
                "Failed to delete file from S3",
                extra={
                    'key': key,
                    'error': str(e),
                    'error_code': e.response['Error']['Code']
                },
                exc_info=True
            )
            return False
    
    def get_url(self, file_path: str) -> str | None:
        """Get displayable URL for a file."""
        if not file_path:
            return None
        
        # Already a full URL, return as-is
        if file_path.startswith(('http://', 'https://')):
            return file_path
        
        # Assume it's a key, construct URL
        return self._get_url(file_path)
    
    def exists(self, file_path: str) -> bool:
        """Check if file exists in S3."""
        if not file_path:
            return False
        
        key = self._extract_key_from_url(file_path)
        if not key:
            key = file_path  # Assume it's already a key
        
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise  # Re-raise other errors