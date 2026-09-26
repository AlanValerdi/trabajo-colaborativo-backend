from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.models.specialty import IncidentCategoryEnum


class ReportStatusEnum(str, Enum):
    REPORTADA = "reportada"
    VALIDADA = "validada"
    ASIGNADA = "asignada"
    EN_PROGRESO = "en_progreso"
    EN_VALIDACION = "en_validacion"
    RESUELTA = "resuelta"
    CERRADA = "cerrada"
    BLOQUEADA = "bloqueada"
    REABIERTA = "reabierta"


class ReportPriorityEnum(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    folio: str = Field(nullable=False, unique=True, index=True, max_length=32)
    title: str = Field(nullable=False, max_length=255)
    description: str = Field(nullable=False)

    campus_label: str = Field(nullable=False, max_length=255)
    faculty_label: str = Field(default="", nullable=False, max_length=255)
    space_label: str = Field(nullable=False, max_length=255)

    campus_id: Optional[int] = Field(default=None, foreign_key="campuses.id", index=True)
    faculty_id: Optional[int] = Field(default=None, foreign_key="faculties.id", index=True)
    location_id: Optional[int] = Field(default=None, foreign_key="locations.id", index=True)

    status: ReportStatusEnum = Field(
        default=ReportStatusEnum.REPORTADA,
        sa_column=Column(
            SAEnum(
                ReportStatusEnum,
                values_callable=lambda obj: [e.value for e in obj],
                name="reportstatusenum",
            ),
            nullable=False,
            server_default="reportada",
        ),
    )

    category: Optional[IncidentCategoryEnum] = Field(
        default=None,
        sa_column=Column(
            SAEnum(
                IncidentCategoryEnum,
                values_callable=lambda obj: [e.value for e in obj],
                name="incidentcategoryenum",
            ),
            nullable=True,
        ),
    )
    specialty_id: Optional[int] = Field(default=None, foreign_key="specialties.id", index=True)
    assignee_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    assigned_at: Optional[datetime] = Field(default=None)

    image_url: Optional[str] = Field(default=None, max_length=1024)
    author_id: int = Field(foreign_key="users.id", nullable=False, index=True)

    classified: bool = Field(default=False, nullable=False)
    priority: Optional[ReportPriorityEnum] = Field(
        default=None,
        sa_column=Column(
            SAEnum(ReportPriorityEnum, values_callable=lambda obj: [e.value for e in obj]),
            nullable=True,
        ),
    )
    awaiting_validation: bool = Field(default=False, nullable=False)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
