from dataclasses import dataclass, field
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlmodel import select

from app.models.collaboration import CollaborationStatusEnum, ReportCollaboration
from app.models.comment import Comment
from app.models.evidence import ReportEvidence
from app.models.report import Report, ReportStatusEnum
from app.models.report_assignment import ReportAssignment
from app.models.report_status_event import ReportStatusEvent
from app.models.specialty import Specialty
from app.models.technical import Diagnosis, WorkLog
from app.models.user import User
from app.schemas.history import ActivityEntry, HistoryEntry, ParticipantRead

_STATUS_LABELS = {
    ReportStatusEnum.REPORTADA: "Reportada",
    ReportStatusEnum.VALIDADA: "Validada",
    ReportStatusEnum.ASIGNADA: "Asignada",
    ReportStatusEnum.EN_PROGRESO: "En progreso",
    ReportStatusEnum.EN_VALIDACION: "En validación",
    ReportStatusEnum.RESUELTA: "Resuelta",
    ReportStatusEnum.CERRADA: "Cerrada",
    ReportStatusEnum.BLOQUEADA: "Bloqueada",
    ReportStatusEnum.REABIERTA: "Reabierta",
}

_COLLAB_LABELS = {
    CollaborationStatusEnum.SOLICITADA: "solicitada",
    CollaborationStatusEnum.ACEPTADA: "aceptada",
    CollaborationStatusEnum.COMPLETADA: "completada",
    CollaborationStatusEnum.RECHAZADA: "rechazada",
}


def _get_report(db: Session, folio: str) -> Report:
    report = db.scalar(select(Report).where(Report.folio == folio))
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un reporte con ese folio",
        )
    return report


def _user_names(db: Session, user_ids: set[int]) -> dict[int, str]:
    if not user_ids:
        return {}
    users = db.scalars(select(User).where(User.id.in_(user_ids))).all()
    return {user.id: user.name for user in users}


def _specialty_names(db: Session, specialty_ids: set[int]) -> dict[int, str]:
    if not specialty_ids:
        return {}
    rows = db.scalars(select(Specialty).where(Specialty.id.in_(specialty_ids))).all()
    return {row.id: row.name for row in rows}


def _truncate(text: str, limit: int = 120) -> str:
    text = text.strip()
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


@dataclass
class _Rows:
    """Filas de origen de las que se arma el historial."""

    status_events: list = field(default_factory=list)
    assignments: list = field(default_factory=list)
    comments: list = field(default_factory=list)
    diagnoses: list = field(default_factory=list)
    work_logs: list = field(default_factory=list)
    evidences: list = field(default_factory=list)
    collaborations: list = field(default_factory=list)

    def report_ids(self) -> set[int]:
        ids: set[int] = set()
        for group in (
            self.status_events,
            self.assignments,
            self.comments,
            self.diagnoses,
            self.work_logs,
            self.evidences,
            self.collaborations,
        ):
            ids.update(row.report_id for row in group)
        return ids


def _load_rows(
    db: Session,
    report_ids: list[int] | None,
    limit: int | None = None,
) -> _Rows:
    """
    Carga las filas de cada fuente de eventos.

    - report_ids: restringe a esos reportes; None significa todos (feed global).
    - limit: si se indica, trae solo las `limit` filas más recientes de cada
      fuente. Basta con eso para armar los `limit` eventos más recientes del
      feed sin leer toda la base de datos (HU-21).
    """

    def fetch(model, ts_column):
        stmt = select(model)
        if report_ids is not None:
            stmt = stmt.where(model.report_id.in_(report_ids))
        if limit is not None:
            stmt = stmt.order_by(ts_column.desc()).limit(limit)
        return list(db.scalars(stmt).all())

    return _Rows(
        status_events=fetch(ReportStatusEvent, ReportStatusEvent.created_at),
        assignments=fetch(ReportAssignment, ReportAssignment.assigned_at),
        comments=fetch(Comment, Comment.created_at),
        diagnoses=fetch(Diagnosis, Diagnosis.created_at),
        work_logs=fetch(WorkLog, WorkLog.created_at),
        evidences=fetch(ReportEvidence, ReportEvidence.created_at),
        # updated_at >= created_at: cubre tanto la solicitud como su respuesta.
        collaborations=fetch(ReportCollaboration, ReportCollaboration.updated_at),
    )


def _collect_entries(
    db: Session,
    reports: list[Report],
) -> list[tuple[Report, HistoryEntry]]:
    """Entradas de historial completas de uno o varios reportes."""
    report_ids = [report.id for report in reports]
    if not report_ids:
        return []
    return _entries_from_rows(db, reports, _load_rows(db, report_ids))


def _entries_from_rows(
    db: Session,
    reports: list[Report],
    rows: _Rows,
) -> list[tuple[Report, HistoryEntry]]:
    """
    Construye las entradas de historial a partir de las filas cargadas.
    Regresa pares (reporte, entrada) para que el feed global (HU-21)
    pueda anotar folio y título.
    """
    report_map = {report.id: report for report in reports}
    status_events = rows.status_events
    assignments = rows.assignments
    comments = rows.comments
    diagnoses = rows.diagnoses
    work_logs = rows.work_logs
    evidences = rows.evidences
    collaborations = rows.collaborations

    user_ids: set[int] = {report.author_id for report in reports}
    user_ids.update(event.actor_id for event in status_events)
    user_ids.update(row.assignee_id for row in assignments)
    user_ids.update(row.assigned_by_id for row in assignments)
    user_ids.update(row.user_id for row in comments)
    user_ids.update(row.author_id for row in diagnoses)
    user_ids.update(row.author_id for row in work_logs)
    user_ids.update(row.uploader_id for row in evidences)
    user_ids.update(row.requested_by_id for row in collaborations)
    user_ids.update(
        row.responded_by_id for row in collaborations if row.responded_by_id is not None
    )
    names = _user_names(db, user_ids)

    specialty_ids: set[int] = set()
    for row in collaborations:
        specialty_ids.add(row.to_specialty_id)
        if row.from_specialty_id is not None:
            specialty_ids.add(row.from_specialty_id)
    specialties = _specialty_names(db, specialty_ids)

    def name_of(user_id: int | None) -> str:
        if user_id is None:
            return "Sistema"
        return names.get(user_id, "Usuario")

    entries: list[tuple[Report, HistoryEntry]] = []

    def add(
        report_id: int,
        type_: str,
        timestamp: datetime,
        actor_id: int | None,
        summary: str,
        detail: dict | None = None,
    ) -> None:
        entries.append(
            (
                report_map[report_id],
                HistoryEntry(
                    type=type_,
                    timestamp=timestamp,
                    actor_id=actor_id,
                    actor_name=name_of(actor_id),
                    summary=summary,
                    detail=detail,
                ),
            )
        )

    for report in reports:
        add(
            report.id,
            "creacion",
            report.created_at,
            report.author_id,
            f"{name_of(report.author_id)} reportó la incidencia",
        )

    for event in status_events:
        detail = {
            "fromStatus": event.from_status.value,
            "toStatus": event.to_status.value,
        }
        if event.comment:
            detail["comment"] = event.comment
        summary = (
            f"{name_of(event.actor_id)} cambió el estado de "
            f"{_STATUS_LABELS[event.from_status]} a {_STATUS_LABELS[event.to_status]}"
        )
        if event.to_status == ReportStatusEnum.BLOQUEADA and event.comment:
            summary = f"{name_of(event.actor_id)} bloqueó la incidencia: {_truncate(event.comment)}"
        add(event.report_id, "estado", event.created_at, event.actor_id, summary, detail)

    for row in assignments:
        add(
            row.report_id,
            "asignacion",
            row.assigned_at,
            row.assigned_by_id,
            f"{name_of(row.assigned_by_id)} asignó la incidencia a {name_of(row.assignee_id)}",
            {"assigneeId": row.assignee_id, "assigneeName": name_of(row.assignee_id)},
        )

    for row in comments:
        add(
            row.report_id,
            "comentario",
            row.created_at,
            row.user_id,
            f"{name_of(row.user_id)} comentó: {_truncate(row.content)}",
            {"commentId": row.id},
        )

    for row in diagnoses:
        add(
            row.report_id,
            "diagnostico",
            row.created_at,
            row.author_id,
            f"{name_of(row.author_id)} registró el diagnóstico: {_truncate(row.root_cause)}",
            {"diagnosisId": row.id},
        )

    for row in work_logs:
        add(
            row.report_id,
            "actividad",
            row.created_at,
            row.author_id,
            f"{name_of(row.author_id)} registró trabajo realizado: {_truncate(row.tasks)}",
            {"workLogId": row.id, "timeMinutes": row.time_minutes},
        )

    for row in evidences:
        stage = f" ({row.stage.value})" if row.stage else ""
        add(
            row.report_id,
            "evidencia",
            row.created_at,
            row.uploader_id,
            f"{name_of(row.uploader_id)} adjuntó evidencia{stage}",
            {"evidenceId": row.id, "fileUrl": row.file_url},
        )

    for row in collaborations:
        to_name = specialties.get(row.to_specialty_id, "otra especialidad")
        add(
            row.report_id,
            "colaboracion",
            row.created_at,
            row.requested_by_id,
            f"{name_of(row.requested_by_id)} solicitó colaboración de {to_name}: {_truncate(row.reason)}",
            {"collaborationId": row.id, "status": row.status.value},
        )
        if row.status != CollaborationStatusEnum.SOLICITADA:
            label = _COLLAB_LABELS[row.status]
            summary = (
                f"{name_of(row.responded_by_id)} marcó como {label} la colaboración con {to_name}"
                if row.responded_by_id is not None
                else f"La colaboración con {to_name} fue {label}"
            )
            add(
                row.report_id,
                "colaboracion",
                row.updated_at,
                row.responded_by_id,
                summary,
                {"collaborationId": row.id, "status": row.status.value},
            )

    return entries


# HU-18 — Consultar historial
def report_history(db: Session, folio: str) -> list[HistoryEntry]:
    report = _get_report(db, folio)
    entries = _collect_entries(db, [report])
    return sorted((entry for _, entry in entries), key=lambda e: e.timestamp)


# HU-14 — Participantes de la incidencia (para autocompletar menciones)
def report_participants(db: Session, folio: str) -> list[ParticipantRead]:
    report = _get_report(db, folio)

    user_ids: set[int] = {report.author_id}
    if report.assignee_id is not None:
        user_ids.add(report.assignee_id)

    user_ids.update(
        db.scalars(
            select(ReportStatusEvent.actor_id).where(
                ReportStatusEvent.report_id == report.id
            )
        ).all()
    )
    user_ids.update(
        db.scalars(
            select(ReportAssignment.assignee_id).where(
                ReportAssignment.report_id == report.id
            )
        ).all()
    )
    user_ids.update(
        db.scalars(
            select(ReportAssignment.assigned_by_id).where(
                ReportAssignment.report_id == report.id
            )
        ).all()
    )
    user_ids.update(
        db.scalars(select(Comment.user_id).where(Comment.report_id == report.id)).all()
    )
    user_ids.update(
        db.scalars(
            select(ReportEvidence.uploader_id).where(
                ReportEvidence.report_id == report.id
            )
        ).all()
    )
    user_ids.update(
        db.scalars(
            select(ReportCollaboration.requested_by_id).where(
                ReportCollaboration.report_id == report.id
            )
        ).all()
    )
    user_ids.update(
        db.scalars(select(Diagnosis.author_id).where(Diagnosis.report_id == report.id)).all()
    )
    user_ids.update(
        db.scalars(select(WorkLog.author_id).where(WorkLog.report_id == report.id)).all()
    )

    users = db.scalars(
        select(User).where(User.id.in_(user_ids)).order_by(User.name.asc())
    ).all()
    return [ParticipantRead(id=user.id, name=user.name) for user in users]


# HU-21 — Mostrar actividad reciente
def recent_activity(db: Session, limit: int = 20) -> list[ActivityEntry]:
    rows = _load_rows(db, None, limit)

    newest = list(
        db.scalars(select(Report).order_by(Report.created_at.desc()).limit(limit)).all()
    )
    known = {report.id for report in newest}
    missing = rows.report_ids() - known
    extra = (
        list(db.scalars(select(Report).where(Report.id.in_(missing))).all())
        if missing
        else []
    )

    entries = _entries_from_rows(db, newest + extra, rows)
    entries.sort(key=lambda pair: pair[1].timestamp, reverse=True)

    feed: list[ActivityEntry] = []
    for report, entry in entries[:limit]:
        feed.append(
            ActivityEntry(
                **entry.model_dump(by_alias=False),
                report_folio=report.folio,
                report_title=report.title,
            )
        )
    return feed
