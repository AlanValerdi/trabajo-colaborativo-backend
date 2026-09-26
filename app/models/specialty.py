from enum import Enum
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class IncidentCategoryEnum(str, Enum):
    INFRAESTRUCTURA = "infraestructura"
    ELECTRICIDAD = "electricidad"
    AGUA = "agua"
    TI = "ti"
    MOBILIARIO = "mobiliario"
    LIMPIEZA = "limpieza"
    SEGURIDAD = "seguridad"
    CLIMATIZACION = "climatizacion"
    OTRO = "otro"


class Specialty(SQLModel, table=True):
    __tablename__ = "specialties"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(nullable=False, unique=True, index=True, max_length=32)
    name: str = Field(nullable=False, max_length=255)
    category: IncidentCategoryEnum = Field(
        sa_column=Column(
            SAEnum(
                IncidentCategoryEnum,
                values_callable=lambda obj: [e.value for e in obj],
                name="incidentcategoryenum",
            ),
            nullable=False,
            unique=True,
        ),
    )
