from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.collaboration import (
    CollaborationCreate,
    CollaborationRead,
    CollaborationStatusUpdate,
)
from app.services import collaboration as collaboration_service

router = APIRouter()
collaboration_router = APIRouter()


# HU-16 — Transferir/colaborar entre áreas
@router.post(
    "/{folio}/collaborations",
    response_model=CollaborationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Solicitar colaboración de otra especialidad (HU-16)",
)
def request_collaboration(
    folio: str,
    payload: CollaborationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    La colaboración no crea una incidencia nueva: queda vinculada al mismo
    folio para conservar un único historial.
    """
    return collaboration_service.request_collaboration(db, folio, current_user, payload)


@router.get(
    "/{folio}/collaborations",
    response_model=list[CollaborationRead],
    summary="Listar colaboraciones de una incidencia (HU-16)",
)
def list_collaborations(
    folio: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return collaboration_service.list_collaborations(db, folio)


@collaboration_router.patch(
    "/{collaboration_id}",
    response_model=CollaborationRead,
    summary="Aceptar, completar o rechazar una colaboración (HU-16)",
)
def update_collaboration(
    collaboration_id: int,
    payload: CollaborationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return collaboration_service.update_collaboration_status(
        db, collaboration_id, current_user, payload
    )
