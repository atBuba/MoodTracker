import io
import logging
import uuid
from datetime import timedelta

from miniopy_async import Minio

from app.config import settings

logger = logging.getLogger(__name__)

BUCKET_NAME = "memes"


class MinioService:
    def __init__(self) -> None:
        url = settings.minio_url.replace("http://", "").replace("https://", "")
        secure = settings.minio_url.startswith("https://")
        self._client = Minio(
            url,
            access_key=settings.minio_user,
            secret_key=settings.minio_password,
            secure=secure,
        )

    async def ensure_bucket(self) -> None:
        """Create the memes bucket if it doesn't exist."""
        try:
            exists = await self._client.bucket_exists(BUCKET_NAME)
            if not exists:
                await self._client.make_bucket(BUCKET_NAME)
                logger.info("Created MinIO bucket: %s", BUCKET_NAME)
        except Exception:
            logger.exception("Failed to ensure MinIO bucket")

    async def upload_image(self, image_data: bytes, content_type: str = "image/png") -> str:
        """Upload image bytes to MinIO and return the presigned URL."""
        await self.ensure_bucket()

        ext = "png" if "png" in content_type else "jpg"
        object_name = f"{uuid.uuid4()}.{ext}"

        await self._client.put_object(
            BUCKET_NAME,
            object_name,
            data=io.BytesIO(image_data),
            length=len(image_data),
            content_type=content_type,
        )
        logger.info("Uploaded image to MinIO: %s/%s", BUCKET_NAME, object_name)

        url = await self._client.presigned_get_object(
            BUCKET_NAME,
            object_name,
            expires=timedelta(days=7),
        )
        return url


minio_service = MinioService()
