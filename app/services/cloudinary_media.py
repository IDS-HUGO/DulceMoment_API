import cloudinary
import cloudinary.uploader
from io import BytesIO
from pathlib import Path
from secrets import token_hex
from urllib.parse import urlparse

from app.core.config import settings


MEDIA_DIR = Path(__file__).resolve().parents[2] / "media" / "uploads"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


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

    normalized_file_obj = BytesIO(file_obj) if isinstance(file_obj, bytes) else file_obj

    _configure_cloudinary()
    response = cloudinary.uploader.upload(
        normalized_file_obj,
        folder=settings.cloudinary_folder,
        resource_type="image",
        filename_override=filename,
    )
    return response["secure_url"], response["public_id"]


def save_local_image_file(file_bytes: bytes, filename: str | None = None) -> tuple[str, str]:
    if not file_bytes:
        raise ValueError("No se recibió contenido de imagen")

    parsed_ext = Path(filename or "").suffix.lower() if filename else ""
    safe_ext = parsed_ext if parsed_ext in {".jpg", ".jpeg", ".png", ".webp", ".gif"} else ".jpg"
    public_id = f"local_{token_hex(8)}"
    file_path = MEDIA_DIR / f"{public_id}{safe_ext}"
    file_path.write_bytes(file_bytes)
    return f"/media/uploads/{file_path.name}", public_id


def normalize_external_image_url(source_url: str) -> str:
    parsed = urlparse(source_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL de imagen inválida")
    return source_url.strip()
