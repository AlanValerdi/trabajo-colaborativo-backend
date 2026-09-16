import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlmodel import select

from app.models.report import Report, ReportStatusEnum
from app.models.user import User
from app.schemas.report import ReportAuthor, ReportCreate, ReportRead, ReportUpdate


def _generate_folio() -> str:
    return f"reporte-{secrets.token_hex(4)}"


def _author_for(user: User | None, author_id: int) -> ReportAuthor:
    if user is None:
        return ReportAuthor(id=author_id, name="Usuario")
    return ReportAuthor(id=user.id, name=user.name)


def serialize_report(report: Report, user: User | None) -> ReportRead:
    return ReportRead(
        id=report.id,
        folio=report.folio,
        title=report.title,
        description=report.description,
        campus_label=report.campus_label,
        space_label=report.space_label,
        status=report.status,
        image_url=report.image_url,
        author_id=report.author_id,
        author=_author_for(user, report.author_id),
        classified=report.classified,
        priority=report.priority,
        awaiting_validation=report.awaiting_validation,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


def serialize_reports(db: Session, reports: list[Report]) -> list[ReportRead]:
    if not reports:
        return []

    author_ids = {report.author_id for report in reports}
    users = db.scalars(select(User).where(User.id.in_(author_ids))).all()
    user_map = {user.id: user for user in users}
    return [serialize_report(report, user_map.get(report.author_id)) for report in reports]


def create_report(db: Session, author_id: int, report_in: ReportCreate) -> ReportRead:
    for _ in range(10):
        folio = _generate_folio()
        existing = db.scalar(select(Report).where(Report.folio == folio))
        if existing is None:
            break
    else:
        raise RuntimeError("No se pudo generar un folio único")

    report = Report(
        folio=folio,
        title=report_in.title,
        description=report_in.description,
        campus_label=report_in.campus_label,
        space_label=report_in.space_label,
        image_url=report_in.image_url,
        author_id=author_id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    author = db.get(User, author_id)
    return serialize_report(report, author)


def list_reports(db: Session) -> list[ReportRead]:
    reports = list(db.scalars(select(Report).order_by(Report.id.desc())).all())
    return serialize_reports(db, reports)


def get_report(db: Session, folio: str) -> ReportRead | None:
    report = db.scalar(select(Report).where(Report.folio == folio))
    if report is None:
        return None
    author = db.get(User, report.author_id)
    return serialize_report(report, author)


def _get_report_for_mutation(db: Session, folio: str, author_id: int) -> Report:
    report = db.scalar(select(Report).where(Report.folio == folio))
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un reporte con ese folio",
        )
    if report.author_id != author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar este reporte",
        )
    if report.status != ReportStatusEnum.CREADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se pueden modificar reportes en estado Creado",
        )
    return report


def update_report(
    db: Session,
    folio: str,
    author_id: int,
    report_in: ReportUpdate,
) -> ReportRead:
    report = _get_report_for_mutation(db, folio, author_id)
    report.title = report_in.title
    report.description = report_in.description
    report.campus_label = report_in.campus_label
    report.space_label = report_in.space_label
    report.image_url = report_in.image_url
    report.updated_at = datetime.now(timezone.utc)
    db.add(report)
    db.commit()
    db.refresh(report)
    author = db.get(User, author_id)
    return serialize_report(report, author)


def delete_report(db: Session, folio: str, author_id: int) -> None:
    report = _get_report_for_mutation(db, folio, author_id)
    db.delete(report)
    db.commit()
