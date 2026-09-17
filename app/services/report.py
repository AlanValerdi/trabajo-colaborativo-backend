import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlmodel import select

from app.models.campus import Campus
from app.models.faculty import Faculty
from app.models.location import Location
from app.models.report import Report, ReportStatusEnum
from app.models.user import User
from app.schemas.report import ReportAuthor, ReportCreate, ReportRead, ReportUpdate


def _generate_folio() -> str:
    return f"reporte-{secrets.token_hex(4)}"


def _author_for(user: User | None, author_id: int) -> ReportAuthor:
    if user is None:
        return ReportAuthor(id=author_id, name="Usuario")
    return ReportAuthor(id=user.id, name=user.name)


def _resolve_hierarchy(
    db: Session,
    campus_id: int,
    faculty_id: int,
    location_id: int,
) -> tuple[Campus, Faculty, Location]:
    campus = db.get(Campus, campus_id)
    if campus is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campus no encontrado",
        )

    faculty = db.get(Faculty, faculty_id)
    if faculty is None or faculty.campus_id != campus_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La facultad no pertenece al campus seleccionado",
        )

    location = db.get(Location, location_id)
    if location is None or location.faculty_id != faculty_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La ubicación no pertenece a la facultad seleccionada",
        )

    return campus, faculty, location


def serialize_report(report: Report, user: User | None) -> ReportRead:
    return ReportRead(
        id=report.id,
        folio=report.folio,
        title=report.title,
        description=report.description,
        campus_label=report.campus_label,
        faculty_label=report.faculty_label,
        space_label=report.space_label,
        campus_id=report.campus_id,
        faculty_id=report.faculty_id,
        location_id=report.location_id,
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
    campus, faculty, location = _resolve_hierarchy(
        db,
        report_in.campus_id,
        report_in.faculty_id,
        report_in.location_id,
    )

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
        campus_label=campus.name,
        faculty_label=faculty.name,
        space_label=location.name,
        campus_id=campus.id,
        faculty_id=faculty.id,
        location_id=location.id,
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
    campus, faculty, location = _resolve_hierarchy(
        db,
        report_in.campus_id,
        report_in.faculty_id,
        report_in.location_id,
    )

    report.title = report_in.title
    report.description = report_in.description
    report.campus_label = campus.name
    report.faculty_label = faculty.name
    report.space_label = location.name
    report.campus_id = campus.id
    report.faculty_id = faculty.id
    report.location_id = location.id
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
