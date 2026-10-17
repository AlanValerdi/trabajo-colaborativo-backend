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

ALLOWED_EVIDENCE_TYPES = {
    **ALLOWED_CONTENT_TYPES,
    "application/pdf": ".pdf",
}
MAX_EVIDENCE_SIZE_BYTES = 10 * 1024 * 1024


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


async def save_evidence_file(file: UploadFile, upload_dir: Path, public_base_url: str) -> str:
    """Guarda una fotografía o documento de evidencia (HU-17)."""
    content_type = file.content_type or ""
    if content_type not in ALLOWED_EVIDENCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de archivo no permitido. Usa JPEG, PNG, WEBP, GIF o PDF.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo de evidencia está vacío.",
        )
    if len(content) > MAX_EVIDENCE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La evidencia no puede superar 10 MB.",
        )

    evidences_dir = upload_dir / "evidences"
    evidences_dir.mkdir(parents=True, exist_ok=True)

    extension = ALLOWED_EVIDENCE_TYPES[content_type]
    filename = f"{uuid4().hex}{extension}"
    destination = evidences_dir / filename
    destination.write_bytes(content)

    base = public_base_url.rstrip("/")
    return f"{base}/uploads/evidences/{filename}"
