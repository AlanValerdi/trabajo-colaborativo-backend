from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.history import ActivityEntry, HistoryEntry, ParticipantRead
from app.services import history as history_service

router = APIRouter()
activity_router = APIRouter()


# HU-18 — Consultar historial
@router.get(
    "/{folio}/history",
    response_model=list[HistoryEntry],
    summary="Historial cronológico completo de una incidencia (HU-18)",
)
def report_history(
    folio: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """
    Línea de tiempo unificada: creación, cambios de estado, asignaciones,
    comentarios, diagnóstico, actividades, evidencias y colaboraciones.
    """
    return history_service.report_history(db, folio)


# HU-14 — Participantes para autocompletar menciones
@router.get(
    "/{folio}/participants",
    response_model=list[ParticipantRead],
    summary="Participantes de la incidencia, para menciones (HU-14)",
)
def report_participants(
    folio: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """
    Autor, asignado y toda persona que haya intervenido (comentarios,
    eventos, evidencias, colaboraciones, diagnóstico, bitácora).
    Accesible a cualquier usuario autenticado.
    """
    return history_service.report_participants(db, folio)


# HU-21 — Mostrar actividad reciente
@activity_router.get(
    "/recent",
    response_model=list[ActivityEntry],
    summary="Actividad reciente de todas las incidencias (HU-21)",
)
def recent_activity(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reportantes y técnicos solo ven la actividad de sus propias incidencias;
    responsables, coordinadores, administradores y validadores ven todo.
    """
    return history_service.recent_activity(db, current_user, limit)
