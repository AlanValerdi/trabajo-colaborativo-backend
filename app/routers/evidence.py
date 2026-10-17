from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.evidence import EvidenceStageEnum
from app.models.user import User
from app.schemas.evidence import EvidenceRead
from app.services import evidence as evidence_service

router = APIRouter()


# HU-17 — Adjuntar evidencia
@router.post(
    "/{folio}/evidences",
    response_model=EvidenceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Adjuntar fotografía o documento de evidencia (HU-17)",
)
async def create_evidence(
    folio: str,
    file: UploadFile = File(...),
    caption: Optional[str] = Form(default=None, max_length=500),
    stage: Optional[EvidenceStageEnum] = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await evidence_service.create_evidence(
        db,
        folio,
        current_user,
        file,
        caption,
        stage,
    )


@router.get(
    "/{folio}/evidences",
    response_model=list[EvidenceRead],
    summary="Listar evidencias de una incidencia (HU-17)",
)
def list_evidences(
    folio: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return evidence_service.list_evidences(db, folio)
