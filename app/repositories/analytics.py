"""SQL queries for reporting; one row per incident, no per-row queries."""
from datetime import datetime, time, timedelta
from sqlalchemy import case, func, select
from app.models.attention_evaluation import AttentionEvaluation
from app.models.report import Report
from app.models.report_status_event import ReportStatusEvent
from app.models.specialty import Specialty
from app.models.user import User


def clauses(filters):
    result = []
    if filters.start_date:
        result.append(Report.created_at >= datetime.combine(filters.start_date, time.min))
    if filters.end_date:
        result.append(Report.created_at < datetime.combine(filters.end_date + timedelta(days=1), time.min))
    for name in ('campus_id', 'specialty_id', 'assignee_id', 'status', 'priority'):
        value = getattr(filters, name)
        if value is not None:
            result.append(getattr(Report, name) == value)
    return result


def milestone_columns():
    event = ReportStatusEvent
    return (
        func.min(case((event.to_status == 'en_progreso', event.created_at))).label('started_at'),
        func.max(case((event.to_status == 'resuelta', event.created_at))).label('resolved_at'),
        func.max(case((event.to_status == 'cerrada', event.created_at))).label('closed_at'),
    )


def get_milestones(db, report_id):
    return db.execute(select(*milestone_columns()).where(ReportStatusEvent.report_id == report_id)).one()


def statement(filters):
    event = ReportStatusEvent
    milestones = select(event.report_id, *milestone_columns()).group_by(event.report_id).subquery()
    return select(
        Report, Specialty.name.label('specialty'), User.name.label('assignee'),
        AttentionEvaluation.rating, milestones.c.started_at,
        milestones.c.resolved_at, milestones.c.closed_at,
    ).outerjoin(Specialty, Report.specialty_id == Specialty.id).outerjoin(
        User, Report.assignee_id == User.id,
    ).outerjoin(AttentionEvaluation, Report.id == AttentionEvaluation.report_id).outerjoin(
        milestones, Report.id == milestones.c.report_id,
    ).where(*clauses(filters))


def rows(db, filters, limit=None, offset=0):
    query = statement(filters).order_by(Report.created_at.desc(), Report.id.desc())
    if limit is not None:
        query = query.limit(limit).offset(offset)
    return db.execute(query.execution_options(yield_per=500))


def count(db, filters):
    return db.scalar(select(func.count()).select_from(Report).where(*clauses(filters)))


def get_report(db, folio, lock=False):
    query = select(Report).where(Report.folio == folio)
    return db.scalar(query.with_for_update() if lock else query)


def get_evaluation(db, report_id):
    return db.scalar(select(AttentionEvaluation).where(AttentionEvaluation.report_id == report_id))
