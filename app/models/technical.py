from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Diagnosis(SQLModel, table=True):
    __tablename__ = "diagnoses"

    id: Optional[int] = Field(default=None, primary_key=True)

    report_id: int = Field(
        foreign_key="reports.id",
        nullable=False,
        index=True,
        unique=True,
    )

    author_id: int = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
    )

    evaluation: str = Field(nullable=False)
    root_cause: str = Field(nullable=False)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class WorkLog(SQLModel, table=True):
    __tablename__ = "work_logs"

    id: Optional[int] = Field(default=None, primary_key=True)

    report_id: int = Field(
        foreign_key="reports.id",
        nullable=False,
        index=True,
    )

    author_id: int = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
    )

    tasks: str = Field(nullable=False)
    materials: str = Field(nullable=False)
    time_minutes: int = Field(nullable=False)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )