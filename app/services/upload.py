from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024


async def save_report_image(file: UploadFile, upload_dir: Path, public_base_url: str) -> str:
    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de imagen no permitido. Usa JPEG, PNG, WEBP o GIF.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo de imagen está vacío.",
        )
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La imagen no puede superar 5 MB.",
        )

    reports_dir = upload_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    extension = ALLOWED_CONTENT_TYPES[content_type]
    filename = f"{uuid4().hex}{extension}"
    destination = reports_dir / filename
    destination.write_bytes(content)

    base = public_base_url.rstrip("/")
    return f"{base}/uploads/reports/{filename}"
