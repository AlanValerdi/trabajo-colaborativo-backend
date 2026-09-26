from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.models.report import ReportStatusEnum


class ReportAssignment(SQLModel, table=True):
    __tablename__ = "report_assignments"

    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="reports.id", nullable=False, index=True)
    assignee_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    assigned_by_id: int = Field(foreign_key="users.id", nullable=False)
    assigned_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    status: ReportStatusEnum = Field(
        sa_column=Column(
            SAEnum(
                ReportStatusEnum,
                values_callable=lambda obj: [e.value for e in obj],
                name="reportstatusenum",
            ),
            nullable=False,
        ),
    )
    specialty_id: int = Field(foreign_key="specialties.id", nullable=False, index=True)
