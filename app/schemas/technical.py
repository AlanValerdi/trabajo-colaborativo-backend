from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class TechnicalAuthor(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: int
    name: str


# HU-11 — Registrar diagnóstico
class DiagnosisCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    evaluation: str = Field(min_length=1)
    root_cause: str = Field(min_length=1)


class DiagnosisRead(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: int
    report_id: int
    author_id: int
    author: TechnicalAuthor
    evaluation: str
    root_cause: str
    created_at: datetime


# HU-12 — Registrar actividades realizadas
class WorkLogCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    tasks: str = Field(min_length=1)
    materials: str = Field(min_length=1)
    time_minutes: int = Field(gt=0)


class WorkLogRead(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: int
    report_id: int
    author_id: int
    author: TechnicalAuthor
    tasks: str
    materials: str
    time_minutes: int
    created_at: datetime