from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.technical import (
    DiagnosisCreate,
    DiagnosisRead,
    WorkLogCreate,
    WorkLogRead,
)
from app.services import technical as technical_service

router = APIRouter()


# HU-11 — Registrar diagnóstico
@router.post(
    "/{folio}/diagnosis",
    response_model=DiagnosisRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar diagnóstico técnico (HU-11)",
)
def create_diagnosis(
    folio: str,
    diagnosis_in: DiagnosisCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.TECNICO)),
):
    return technical_service.create_diagnosis(
        db,
        folio,
        current_user.id,
        diagnosis_in,
    )


@router.get(
    "/{folio}/diagnosis",
    response_model=DiagnosisRead,
    summary="Consultar diagnóstico técnico (HU-11)",
)
def get_diagnosis(
    folio: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    diagnosis = technical_service.get_diagnosis(db, folio)

    if diagnosis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Este reporte todavía no tiene diagnóstico",
        )

    return diagnosis


# HU-12 — Registrar actividades
@router.post(
    "/{folio}/work-logs",
    response_model=WorkLogRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar actividad técnica (HU-12)",
)
def create_work_log(
    folio: str,
    work_log_in: WorkLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.TECNICO)),
):
    return technical_service.create_work_log(
        db,
        folio,
        current_user.id,
        work_log_in,
    )


@router.get(
    "/{folio}/work-logs",
    response_model=list[WorkLogRead],
    summary="Consultar bitácora técnica (HU-12)",
)
def list_work_logs(
    folio: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return technical_service.list_work_logs(db, folio)