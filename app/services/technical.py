from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlmodel import select

from app.models.report import Report
from app.models.technical import Diagnosis, WorkLog
from app.models.user import User
from app.schemas.technical import (
    DiagnosisCreate,
    DiagnosisRead,
    TechnicalAuthor,
    WorkLogCreate,
    WorkLogRead,
)


def _get_report(db: Session, folio: str) -> Report:
    report = db.scalar(select(Report).where(Report.folio == folio))

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un reporte con ese folio",
        )

    return report


def _get_report_for_assignee(
    db: Session,
    folio: str,
    technician_id: int,
) -> Report:
    report = _get_report(db, folio)

    if report.assignee_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El reporte todavía no tiene un técnico asignado",
        )

    if report.assignee_id != technician_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el técnico asignado puede registrar información técnica",
        )

    return report


def _author_for(user: User | None, author_id: int) -> TechnicalAuthor:
    if user is None:
        return TechnicalAuthor(
            id=author_id,
            name="Usuario",
        )

    return TechnicalAuthor(
        id=user.id,
        name=user.name,
    )


def _serialize_diagnosis(
    diagnosis: Diagnosis,
    user: User | None,
) -> DiagnosisRead:
    return DiagnosisRead(
        id=diagnosis.id,
        report_id=diagnosis.report_id,
        author_id=diagnosis.author_id,
        author=_author_for(user, diagnosis.author_id),
        evaluation=diagnosis.evaluation,
        root_cause=diagnosis.root_cause,
        created_at=diagnosis.created_at,
    )


def _serialize_work_log(
    work_log: WorkLog,
    user: User | None,
) -> WorkLogRead:
    return WorkLogRead(
        id=work_log.id,
        report_id=work_log.report_id,
        author_id=work_log.author_id,
        author=_author_for(user, work_log.author_id),
        tasks=work_log.tasks,
        materials=work_log.materials,
        time_minutes=work_log.time_minutes,
        created_at=work_log.created_at,
    )


# HU-11 — Registrar diagnóstico
def create_diagnosis(
    db: Session,
    folio: str,
    author_id: int,
    diagnosis_in: DiagnosisCreate,
) -> DiagnosisRead:
    report = _get_report_for_assignee(
        db,
        folio,
        author_id,
    )

    existing = db.scalar(
        select(Diagnosis).where(
            Diagnosis.report_id == report.id
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este reporte ya tiene un diagnóstico registrado",
        )

    diagnosis = Diagnosis(
        report_id=report.id,
        author_id=author_id,
        evaluation=diagnosis_in.evaluation,
        root_cause=diagnosis_in.root_cause,
    )

    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)

    author = db.get(User, author_id)

    return _serialize_diagnosis(
        diagnosis,
        author,
    )


def get_diagnosis(
    db: Session,
    folio: str,
) -> DiagnosisRead | None:
    report = _get_report(db, folio)

    diagnosis = db.scalar(
        select(Diagnosis).where(
            Diagnosis.report_id == report.id
        )
    )

    if diagnosis is None:
        return None

    author = db.get(
        User,
        diagnosis.author_id,
    )

    return _serialize_diagnosis(
        diagnosis,
        author,
    )


# HU-12 — Registrar actividades realizadas
def create_work_log(
    db: Session,
    folio: str,
    author_id: int,
    work_log_in: WorkLogCreate,
) -> WorkLogRead:
    report = _get_report_for_assignee(
        db,
        folio,
        author_id,
    )

    work_log = WorkLog(
        report_id=report.id,
        author_id=author_id,
        tasks=work_log_in.tasks,
        materials=work_log_in.materials,
        time_minutes=work_log_in.time_minutes,
    )

    db.add(work_log)
    db.commit()
    db.refresh(work_log)

    author = db.get(
        User,
        author_id,
    )

    return _serialize_work_log(
        work_log,
        author,
    )


def list_work_logs(
    db: Session,
    folio: str,
) -> list[WorkLogRead]:
    report = _get_report(db, folio)

    work_logs = list(
        db.scalars(
            select(WorkLog)
            .where(WorkLog.report_id == report.id)
            .order_by(
                WorkLog.created_at.asc(),
                WorkLog.id.asc(),
            )
        ).all()
    )

    result: list[WorkLogRead] = []

    for work_log in work_logs:
        author = db.get(
            User,
            work_log.author_id,
        )

        result.append(
            _serialize_work_log(
                work_log,
                author,
            )
        )

    return result