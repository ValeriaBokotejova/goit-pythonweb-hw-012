import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

from app.core.config import settings

# Configure Cloudinary using environment variables
cloudinary.config(
    cloud_name=settings.cloudinary_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)


async def upload_avatar_to_cloudinary(file: UploadFile, public_id: str) -> str:
    """Uploads an avatar image to Cloudinary and returns the secure URL."""
    result = cloudinary.uploader.upload(
        file.file,
        public_id=public_id,
        overwrite=True,
        resource_type="image",
    )
    return result["secure_url"]
