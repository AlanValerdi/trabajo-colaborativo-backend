from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class CollaborationStatusEnum(str, Enum):
    SOLICITADA = "solicitada"
    ACEPTADA = "aceptada"
    COMPLETADA = "completada"
    RECHAZADA = "rechazada"


class ReportCollaboration(SQLModel, table=True):
    """
    Solicitud de colaboración entre áreas (HU-16).
    No crea una incidencia nueva: referencia al mismo reporte para
    conservar un único historial.
    """

    __tablename__ = "report_collaborations"

    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="reports.id", nullable=False, index=True)
    requested_by_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    from_specialty_id: Optional[int] = Field(
        default=None, foreign_key="specialties.id"
    )
    to_specialty_id: int = Field(foreign_key="specialties.id", nullable=False)
    reason: str = Field(nullable=False, max_length=1000)
    # Último usuario que cambió el estado (aceptó, rechazó o completó).
    responded_by_id: Optional[int] = Field(
        default=None, foreign_key="users.id", index=True
    )
    status: CollaborationStatusEnum = Field(
        default=CollaborationStatusEnum.SOLICITADA,
        sa_column=Column(
            SAEnum(
                CollaborationStatusEnum,
                values_callable=lambda obj: [e.value for e in obj],
                name="collaborationstatusenum",
            ),
            nullable=False,
            server_default="solicitada",
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
