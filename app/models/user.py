from __future__ import annotations

from typing import Optional

from enum import Enum 
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

    #   Cambiar optional a required y UUID 
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)

    role: RoleEnum = Field(default=RoleEnum.REPORTANTE, nullable=False)
