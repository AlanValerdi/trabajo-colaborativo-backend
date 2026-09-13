from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class RoleEnum(str, Enum):
    REPORTANTE = "reportante"
    TECNICO = "tecnico"
    RESPONSABLE_AREA = "responsable_area"
    COORDINADOR = "coordinador"
    ADMINISTRADOR = "administrador"
    VALIDADOR = "validador"


class User(SQLModel, table=True):
    __tablename__ = "users"

    # TODO: Cambiar a UUID
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True, index=True)
    password_hash: str = Field(nullable=False)

    # values_callable fuerza a usar los .value ("reportante") en vez del nombre ("REPORTANTE")
    role: RoleEnum = Field(
        default=RoleEnum.REPORTANTE,
        sa_column=Column(
            SAEnum(
                RoleEnum,
                values_callable=lambda obj: [e.value for e in obj],
            ),
            nullable=False,
            server_default="reportante",
        ),
    )

    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
