from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from app.models.collaboration import CollaborationStatusEnum
from app.models.specialty import IncidentCategoryEnum


class CollaborationCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    category: IncidentCategoryEnum
    reason: str = Field(min_length=1, max_length=1000)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("La razón de la colaboración no puede estar vacía")
        return stripped


class CollaborationStatusUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: CollaborationStatusEnum


class CollaborationActor(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    name: str


class CollaborationSpecialty(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    name: str
    category: IncidentCategoryEnum


class CollaborationRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    report_id: int
    report_folio: str
    requested_by_id: int
    requested_by: CollaborationActor
    from_specialty: Optional[CollaborationSpecialty]
    to_specialty: CollaborationSpecialty
    reason: str
    status: CollaborationStatusEnum
    responded_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
