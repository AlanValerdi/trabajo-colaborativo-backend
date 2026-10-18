from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlmodel import select

from app.models.collaboration import CollaborationStatusEnum, ReportCollaboration
from app.models.report import Report, ReportStatusEnum
from app.models.role import RoleEnum
from app.models.specialty import Specialty
from app.models.user import User
from app.schemas.collaboration import (
    CollaborationActor,
    CollaborationCreate,
    CollaborationRead,
    CollaborationSpecialty,
    CollaborationStatusUpdate,
)

_MANAGE_ROLES = {
    RoleEnum.RESPONSABLE_AREA,
    RoleEnum.COORDINADOR,
    RoleEnum.ADMINISTRADOR,
}

_FINAL_STATUSES = {
    CollaborationStatusEnum.COMPLETADA,
    CollaborationStatusEnum.RECHAZADA,
}

_ALLOWED_TRANSITIONS = {
    CollaborationStatusEnum.SOLICITADA: {
        CollaborationStatusEnum.ACEPTADA,
        CollaborationStatusEnum.RECHAZADA,
    },
    CollaborationStatusEnum.ACEPTADA: {
        CollaborationStatusEnum.COMPLETADA,
        CollaborationStatusEnum.RECHAZADA,
    },
}

_COLLABORATION_SOURCES = {
    ReportStatusEnum.ASIGNADA,
    ReportStatusEnum.EN_PROGRESO,
    ReportStatusEnum.BLOQUEADA,
}


def _get_report(db: Session, folio: str) -> Report:
    report = db.scalar(select(Report).where(Report.folio == folio))
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un reporte con ese folio",
        )
    return report


def _specialty_read(specialty: Specialty | None) -> CollaborationSpecialty | None:
    if specialty is None:
        return None
    return CollaborationSpecialty(
        id=specialty.id,
        name=specialty.name,
        category=specialty.category,
    )


def _serialize(
    db: Session,
    collaboration: ReportCollaboration,
    report: Report | None = None,
) -> CollaborationRead:
    if report is None:
        report = db.get(Report, collaboration.report_id)
    requester = db.get(User, collaboration.requested_by_id)
    from_specialty = (
        db.get(Specialty, collaboration.from_specialty_id)
        if collaboration.from_specialty_id is not None
        else None
    )
    to_specialty = db.get(Specialty, collaboration.to_specialty_id)

    return CollaborationRead(
        id=collaboration.id,
        report_id=collaboration.report_id,
        report_folio=report.folio if report else "",
        requested_by_id=collaboration.requested_by_id,
        requested_by=CollaborationActor(
            id=collaboration.requested_by_id,
            name=requester.name if requester else "Usuario",
        ),
        from_specialty=_specialty_read(from_specialty),
        to_specialty=_specialty_read(to_specialty),
        reason=collaboration.reason,
        status=collaboration.status,
        created_at=collaboration.created_at,
        updated_at=collaboration.updated_at,
    )


def _assert_can_request(report: Report, actor: User) -> None:
    is_assignee = report.assignee_id is not None and report.assignee_id == actor.id
    if not (is_assignee or actor.has_any_role(*_MANAGE_ROLES)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el técnico asignado o un responsable puede solicitar colaboración",
        )


# HU-16 — Solicitar colaboración de otra especialidad
def request_collaboration(
    db: Session,
    folio: str,
    actor: User,
    payload: CollaborationCreate,
) -> CollaborationRead:
    report = _get_report(db, folio)
    _assert_can_request(report, actor)

    if report.status not in _COLLABORATION_SOURCES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se puede solicitar colaboración en una incidencia asignada, en progreso o bloqueada",
        )

    target = db.scalar(select(Specialty).where(Specialty.category == payload.category))
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No hay especialidad vinculada a esa categoría",
        )
    if target.id == report.specialty_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La incidencia ya pertenece a esa especialidad",
        )

    open_duplicate = db.scalar(
        select(ReportCollaboration).where(
            ReportCollaboration.report_id == report.id,
            ReportCollaboration.to_specialty_id == target.id,
            ReportCollaboration.status.not_in([s.value for s in _FINAL_STATUSES]),
        )
    )
    if open_duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una solicitud de colaboración abierta con esa especialidad",
        )

    collaboration = ReportCollaboration(
        report_id=report.id,
        requested_by_id=actor.id,
        from_specialty_id=report.specialty_id,
        to_specialty_id=target.id,
        reason=payload.reason,
    )
    db.add(collaboration)
    db.commit()
    db.refresh(collaboration)
    return _serialize(db, collaboration, report)


def list_collaborations(db: Session, folio: str) -> list[CollaborationRead]:
    report = _get_report(db, folio)
    rows = list(
        db.scalars(
            select(ReportCollaboration)
            .where(ReportCollaboration.report_id == report.id)
            .order_by(ReportCollaboration.created_at.asc(), ReportCollaboration.id.asc())
        ).all()
    )
    return [_serialize(db, row, report) for row in rows]


def update_collaboration_status(
    db: Session,
    collaboration_id: int,
    actor: User,
    payload: CollaborationStatusUpdate,
) -> CollaborationRead:
    collaboration = db.get(ReportCollaboration, collaboration_id)
    if collaboration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe esa solicitud de colaboración",
        )

    report = db.get(Report, collaboration.report_id)
    # Solo los roles de supervisión resuelven colaboraciones: el técnico
    # solicita (request_collaboration), pero no las acepta/rechaza/completa.
    if not actor.has_any_role(*_MANAGE_ROLES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un responsable de área, coordinador o administrador puede actualizar la colaboración",
        )

    allowed = _ALLOWED_TRANSITIONS.get(collaboration.status, set())
    if payload.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede pasar la colaboración de {collaboration.status.value} a {payload.status.value}",
        )

    collaboration.status = payload.status
    collaboration.updated_at = datetime.now(timezone.utc)
    db.add(collaboration)
    db.commit()
    db.refresh(collaboration)
    return _serialize(db, collaboration, report)
