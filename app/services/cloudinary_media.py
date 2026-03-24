import cloudinary
import cloudinary.uploader

from app.core.config import settings


def is_cloudinary_configured() -> bool:
    if settings.cloudinary_url:
        return True
    return all(
        [
            settings.cloudinary_cloud_name,
            settings.cloudinary_api_key,
            settings.cloudinary_api_secret,
        ]
    )


def _configure_cloudinary():
    if settings.cloudinary_url:
        cloudinary.config(cloudinary_url=settings.cloudinary_url, secure=True)
    else:
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )


def upload_image_from_url(source_url: str) -> tuple[str, str]:
    if not is_cloudinary_configured():
        raise ValueError("Cloudinary no configurado")

    _configure_cloudinary()
    response = cloudinary.uploader.upload(
        source_url,
        folder=settings.cloudinary_folder,
        resource_type="image",
    )
    return response["secure_url"], response["public_id"]


def upload_image_file(file_obj, filename: str | None = None, content_type: str | None = None) -> tuple[str, str]:
    if not is_cloudinary_configured():
        raise ValueError("Cloudinary no configurado")

    _configure_cloudinary()
    response = cloudinary.uploader.upload(
        file_obj,
        folder=settings.cloudinary_folder,
        resource_type="image",
        filename_override=filename,
    )
    return response["secure_url"], response["public_id"]
