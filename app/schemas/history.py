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
