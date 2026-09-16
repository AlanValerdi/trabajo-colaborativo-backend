from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.models.report import ReportPriorityEnum, ReportStatusEnum


class ReportUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    title: str
    description: str
    campus_label: str
    space_label: str
    image_url: Optional[str] = None


class ReportCreate(BaseModel):
    """
    Entrada minima para poder crear datos de prueba y validar la consulta (HU-4)
    de punta a punta. El formulario definitivo de alta (HU-05/06) es responsabilidad
    de Equipo 1; cuando conecten el catalogo de Campus/Space (HU-03) esto deberia
    migrar a campusId/spaceId reales en vez de texto libre.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    title: str
    description: str
    campus_label: str
    space_label: str
    image_url: Optional[str] = None


class ReportAuthor(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    name: str


class ReportRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: int
    folio: str
    title: str
    description: str
    campus_label: str
    space_label: str
    status: ReportStatusEnum
    image_url: Optional[str]
    author_id: int
    author: ReportAuthor
    classified: bool
    priority: Optional[ReportPriorityEnum]
    awaiting_validation: bool
    created_at: datetime
    updated_at: datetime
