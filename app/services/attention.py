"""Per-incident attention queries and the evaluation use case."""
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.domain.attention import attention_times
from app.models.attention_evaluation import AttentionEvaluation
from app.models.report import Report, ReportStatusEnum
from app.models.role import RoleEnum
from app.models.user import User
from app.repositories import analytics as repository
from app.schemas.analytics import AttentionTimes, EvaluationCreate, EvaluationRead

MANAGEMENT_ROLES = (RoleEnum.ADMINISTRADOR, RoleEnum.COORDINADOR, RoleEnum.RESPONSABLE_AREA)


def authorized_report(db: Session, folio: str, user: User, lock: bool = False) -> Report:
    report = repository.get_report(db, folio, lock)
    if report is None:
        raise HTTPException(404, 'No existe un reporte con ese folio')
    if report.author_id != user.id and report.assignee_id != user.id and not user.has_any_role(*MANAGEMENT_ROLES):
        raise HTTPException(403, 'No tienes permiso para consultar estos datos')
    return report


def timings(db: Session, folio: str, user: User) -> AttentionTimes:
    report = authorized_report(db, folio, user)
    events = repository.get_milestones(db, report.id)
    return AttentionTimes(**attention_times(report.created_at, report.status, events.started_at,
        events.resolved_at, events.closed_at, datetime.now(timezone.utc)))


def evaluation(db: Session, folio: str, user: User) -> EvaluationRead | None:
    report = authorized_report(db, folio, user)
    result = repository.get_evaluation(db, report.id)
    return EvaluationRead.model_validate(result) if result else None


def create_evaluation(db: Session, folio: str, user: User, data: EvaluationCreate) -> EvaluationRead:
    # Lock the report to serialize concurrent submissions and state transitions.
    report = authorized_report(db, folio, user, lock=True)
    if report.author_id != user.id:
        raise HTTPException(403, 'Solo el autor del reporte puede evaluar la atención')
    if report.status != ReportStatusEnum.CERRADA:
        raise HTTPException(409, 'Solo puedes evaluar una incidencia cerrada')
    if repository.get_evaluation(db, report.id):
        raise HTTPException(409, 'Esta incidencia ya tiene una evaluación')
    result = AttentionEvaluation(report_id=report.id, author_id=user.id, **data.model_dump())
    db.add(result)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Esta incidencia ya tiene una evaluación') from None
    db.refresh(result)
    return EvaluationRead.model_validate(result)
