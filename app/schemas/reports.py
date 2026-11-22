from datetime import datetime

from pydantic import BaseModel

from app.models.report import ReportPriorityEnum, ReportStatusEnum
from app.models.specialty import IncidentCategoryEnum


class ReportSummaryKpis(BaseModel):
    total: int
    open: int
    in_progress: int
    blocked: int
    resolved_closed: int
    average_resolution_hours: float | None


class ReportSummaryItem(BaseModel):
    id: int
    title: str
    category: IncidentCategoryEnum | None
    priority: ReportPriorityEnum | None
    status: ReportStatusEnum
    location_id: int | None
    location: str
    assignee: str | None
    created_at: datetime
    closed_at: datetime | None


class ReportSummary(BaseModel):
    kpis: ReportSummaryKpis
    by_category: list[dict[str, str | int | None]]
    by_status: list[dict[str, str | int]]
    by_priority: list[dict[str, str | int | None]]
    by_building: list[dict[str, str | int | None]]
    total: int
    limit: int
    offset: int
    items: list[ReportSummaryItem]
