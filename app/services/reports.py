from datetime import date, datetime, time, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlmodel import select

from app.models.report import Report, ReportPriorityEnum, ReportStatusEnum
from app.models.report_status_event import ReportStatusEvent
from app.models.specialty import IncidentCategoryEnum
from app.models.user import User
from app.schemas.reports import (
    ReportSummary,
    ReportSummaryItem,
    ReportSummaryKpis,
)

_IN_PROGRESS_STATUSES = {ReportStatusEnum.EN_PROGRESO}
_RESOLVED_STATUSES = {ReportStatusEnum.RESUELTA, ReportStatusEnum.CERRADA}


def _filters(
    start_date: date | None,
    end_date: date | None,
    category_id: IncidentCategoryEnum | None,
    area_id: int | None,
    location_id: int | None,
    building_id: int | None,
    report_status: ReportStatusEnum | None,
    priority: ReportPriorityEnum | None,
):
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="start_date debe ser anterior o igual a end_date",
        )
    if location_id is not None and building_id is not None and location_id != building_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="location_id y building_id deben identificar la misma ubicación",
        )

    clauses = []
    if start_date is not None:
        clauses.append(Report.created_at >= datetime.combine(start_date, time.min))
    if end_date is not None:
        clauses.append(
            Report.created_at < datetime.combine(end_date + timedelta(days=1), time.min)
        )
    if category_id is not None:
        clauses.append(Report.category == category_id)
    if area_id is not None:
        clauses.append(Report.specialty_id == area_id)
    selected_location_id = location_id if location_id is not None else building_id
    if selected_location_id is not None:
        clauses.append(Report.location_id == selected_location_id)
    if report_status is not None:
        clauses.append(Report.status == report_status)
    if priority is not None:
        clauses.append(Report.priority == priority)
    return clauses


def summary(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
    category_id: IncidentCategoryEnum | None = None,
    area_id: int | None = None,
    location_id: int | None = None,
    building_id: int | None = None,
    report_status: ReportStatusEnum | None = None,
    priority: ReportPriorityEnum | None = None,
    limit: int = 50,
    offset: int = 0,
) -> ReportSummary:
    clauses = _filters(
        start_date,
        end_date,
        category_id,
        area_id,
        location_id,
        building_id,
        report_status,
        priority,
    )
    total = db.scalar(
        select(func.count()).select_from(Report).where(*clauses)
    ) or 0

    status_counts = db.execute(
        select(Report.status, func.count(Report.id))
        .where(*clauses)
        .group_by(Report.status)
    ).all()
    status_map = dict(status_counts)

    category_rows = db.execute(
        select(Report.category, func.count(Report.id))
        .where(*clauses)
        .group_by(Report.category)
    ).all()
    priority_rows = db.execute(
        select(Report.priority, func.count(Report.id))
        .where(*clauses)
        .group_by(Report.priority)
    ).all()
    building_rows = db.execute(
        select(Report.location_id, Report.space_label, func.count(Report.id))
        .where(*clauses)
        .group_by(Report.location_id, Report.space_label)
    ).all()

    reports = db.scalars(
        select(Report)
        .where(*clauses)
        .order_by(Report.created_at.desc(), Report.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    assignees = {}
    if reports:
        assignee_ids = {report.assignee_id for report in reports if report.assignee_id}
        if assignee_ids:
            assignees = {
                user.id: user.name
                for user in db.scalars(select(User).where(User.id.in_(assignee_ids))).all()
            }
    resolution_rows = db.execute(
        select(
            Report.id,
            Report.created_at,
            func.max(ReportStatusEvent.created_at),
        )
        .join(ReportStatusEvent, ReportStatusEvent.report_id == Report.id)
        .where(
            *clauses,
            Report.status.in_(_RESOLVED_STATUSES),
            ReportStatusEvent.to_status.in_(_RESOLVED_STATUSES),
        )
        .group_by(Report.id, Report.created_at)
    ).all()
    closed_dates = {report_id: closed_at for report_id, _, closed_at in resolution_rows}
    resolution_hours = [
        (closed_at - created_at).total_seconds() / 3600
        for _, created_at, closed_at in resolution_rows
    ]

    in_progress = sum(status_map.get(value, 0) for value in _IN_PROGRESS_STATUSES)
    blocked = status_map.get(ReportStatusEnum.BLOQUEADA, 0)
    resolved_closed = sum(status_map.get(value, 0) for value in _RESOLVED_STATUSES)

    return ReportSummary(
        kpis=ReportSummaryKpis(
            total=total,
            open=total - resolved_closed,
            in_progress=in_progress,
            blocked=blocked,
            resolved_closed=resolved_closed,
            average_resolution_hours=(
                sum(resolution_hours) / len(resolution_hours) if resolution_hours else None
            ),
        ),
        by_category=[
            {
                "category": category.value if category is not None else None,
                "count": count,
            }
            for category, count in category_rows
        ],
        by_status=[
            {"status": report_status.value, "count": count}
            for report_status, count in status_counts
        ],
        by_priority=[
            {
                "priority": report_priority.value if report_priority is not None else None,
                "count": count,
            }
            for report_priority, count in priority_rows
        ],
        by_building=[
            {"location_id": location_id, "building": label, "count": count}
            for location_id, label, count in building_rows
        ],
        total=total,
        limit=limit,
        offset=offset,
        items=[
            ReportSummaryItem(
                id=report.id,
                title=report.title,
                category=report.category,
                priority=report.priority,
                status=report.status,
                location_id=report.location_id,
                location=report.space_label,
                assignee=assignees.get(report.assignee_id),
                created_at=report.created_at,
                closed_at=closed_dates.get(report.id),
            )
            for report in reports
        ],
    )
