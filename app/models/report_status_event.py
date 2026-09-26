from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.models.report import ReportStatusEnum


def _status_column() -> Column:
    return Column(
        SAEnum(
            ReportStatusEnum,
            values_callable=lambda obj: [e.value for e in obj],
            name="reportstatusenum",
        ),
        nullable=False,
    )


class ReportStatusEvent(SQLModel, table=True):
    __tablename__ = "report_status_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="reports.id", nullable=False, index=True)
    from_status: ReportStatusEnum = Field(sa_column=_status_column())
    to_status: ReportStatusEnum = Field(sa_column=_status_column())
    actor_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    comment: Optional[str] = Field(default=None, max_length=1000)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
