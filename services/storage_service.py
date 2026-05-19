import logging
import boto3
from django.conf import settings
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class StorageService:
    """
    S3-compatible cloud storage service for audio assets.
    Works with DigitalOcean Spaces, AWS S3, or any S3-compatible provider
    by configuring AWS_S3_ENDPOINT_URL.
    """

    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(signature_version='s3v4'),
        )
        self.bucket = settings.AWS_STORAGE_BUCKET_NAME

    def upload_audio(self, file_data: bytes, key: str) -> str:
        """
        Upload an MP3 blob to S3/Spaces and return its public URL.
        The object is set to public-read for CDN delivery.
        """
        logger.info('Uploading audio to %s/%s (%d bytes)', self.bucket, key, len(file_data))

        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=file_data,
            ContentType='audio/mpeg',
            ACL='public-read',
            CacheControl='max-age=31536000',  # 1 year cache
        )

        url = self._build_url(key)
        logger.info('Audio uploaded successfully: %s', url)
        return url

    def delete_file(self, key: str) -> bool:
        """Delete a file from storage. Returns True on success."""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info('Deleted storage object: %s', key)
            return True
        except ClientError as e:
            logger.error('Failed to delete %s: %s', key, e)
            return False

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generate a temporary pre-signed URL for private objects.
        Useful for giving time-limited access to audio files.
        """
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=expires_in,
        )

    def _build_url(self, key: str) -> str:
        """Build the public URL for an object."""
        if settings.AWS_S3_CUSTOM_DOMAIN:
            return f'https://{settings.AWS_S3_CUSTOM_DOMAIN}/{key}'
        if settings.AWS_S3_ENDPOINT_URL:
            return f'{settings.AWS_S3_ENDPOINT_URL}/{self.bucket}/{key}'
        # Standard AWS S3 URL
        region = settings.AWS_S3_REGION_NAME
        return f'https://{self.bucket}.s3.{region}.amazonaws.com/{key}'
