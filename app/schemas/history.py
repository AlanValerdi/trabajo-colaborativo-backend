from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class HistoryEntry(BaseModel):
    """Entrada unificada del historial de una incidencia (HU-18)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    type: str
    timestamp: datetime
    actor_id: Optional[int]
    actor_name: str
    summary: str
    detail: Optional[dict[str, Any]] = None


class ActivityEntry(HistoryEntry):
    """Entrada del feed de actividad reciente (HU-21)."""

    report_folio: str
    report_title: str


class ParticipantRead(BaseModel):
    """Participante de una incidencia, para autocompletar menciones (HU-14)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    name: str


class CategorySummary(BaseModel):
    """Conteo de incidencias por categoría en un espacio físico (HU-26)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    category: str
    count: int


class LocationIncidentItem(BaseModel):
    """Incidencia dentro del historial de un espacio físico (HU-26)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    folio: str
    title: str
    created_at: datetime
    status: str
    category: str
    assigned_tech_name: Optional[str] = None
    diagnosis_summary: Optional[str] = None


class LocationHistoryResponse(BaseModel):
    """Historial consolidado de incidencias de un espacio físico (HU-26)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    location_id: int
    location_name: str
    total_incidents: int
    categories_summary: list[CategorySummary]
    timeline: list[LocationIncidentItem]
