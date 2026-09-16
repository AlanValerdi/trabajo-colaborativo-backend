from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from enum import Enum

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class ReportStatusEnum(str, Enum):
    CREADO = "creado"
    EN_REVISION = "en_revision"
    RESUELTO = "resuelto"


class ReportPriorityEnum(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Folio visible al usuario (formato reporte-{rand}, HU-4).
    folio: str = Field(nullable=False, unique=True, index=True, max_length=32)

    title: str = Field(nullable=False, max_length=255)
    description: str = Field(nullable=False)

    # NOTA: Equipo 1 (HU-03) todavia no entrega el catalogo de Campus/Space.
    # Mientras tanto se guardan como texto libre para no bloquear HU-4.
    # Cuando exista el catalogo, migrar campus_label/space_label a FKs reales
    # (campus_id -> campuses.id, space_id -> spaces.id).
    campus_label: str = Field(nullable=False, max_length=255)
    space_label: str = Field(nullable=False, max_length=255)

    status: ReportStatusEnum = Field(
        default=ReportStatusEnum.CREADO,
        sa_column=Column(
            SAEnum(ReportStatusEnum, values_callable=lambda obj: [e.value for e in obj]),
            nullable=False,
            server_default="creado",
        ),
    )

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
