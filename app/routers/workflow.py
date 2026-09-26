from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.report import ReportRead
from app.schemas.workflow import (
    AssignmentCreate,
    AssignmentRead,
    CategorizeReport,
    SpecialtyRead,
    StatusChange,
    StatusEventRead,
)
from app.services import workflow as workflow_service

router = APIRouter()
specialty_router = APIRouter()


@specialty_router.get("/", response_model=list[SpecialtyRead], summary="Listar especialidades")
def list_specialties(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return workflow_service.list_specialties(db)


@router.post(
    "/{folio}/category",
    response_model=ReportRead,
    summary="Categorizar incidencia (HU-07)",
    dependencies=[Depends(require_roles(RoleEnum.RESPONSABLE_AREA, RoleEnum.ADMINISTRADOR))],
)
def categorize_report(
    folio: str,
    payload: CategorizeReport,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return workflow_service.categorize_report(db, folio, payload, current_user)


@router.post(
    "/{folio}/assignments",
    response_model=ReportRead,
    status_code=status.HTTP_201_CREATED,
    summary="Asignar responsable (HU-09)",
    dependencies=[
        Depends(require_roles(RoleEnum.RESPONSABLE_AREA, RoleEnum.COORDINADOR, RoleEnum.ADMINISTRADOR))
    ],
)
def assign_report(
    folio: str,
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return workflow_service.assign_report(db, folio, payload, current_user)


@router.get(
    "/{folio}/assignments",
    response_model=list[AssignmentRead],
    summary="Historial de asignaciones (HU-09)",
)
def list_assignments(
    folio: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return workflow_service.list_assignments(db, folio)


@router.post(
    "/{folio}/status",
    response_model=ReportRead,
    summary="Cambiar estado de la incidencia (HU-10)",
)
def change_status(
    folio: str,
    payload: StatusChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return workflow_service.change_status(db, folio, payload, current_user)


@router.get(
    "/{folio}/status-events",
    response_model=list[StatusEventRead],
    summary="Trazabilidad de estados (HU-10)",
)
def list_status_events(
    folio: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return workflow_service.list_status_events(db, folio)
