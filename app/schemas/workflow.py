from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

from app.models.report import ReportPriorityEnum, ReportStatusEnum
from app.models.specialty import IncidentCategoryEnum


class SpecialtyRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: int
    code: str
    name: str
    category: IncidentCategoryEnum


class CategorizeReport(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    category: IncidentCategoryEnum
    priority: ReportPriorityEnum


class AssignmentCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    assignee_id: int = Field(gt=0)


class AssignmentRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: int
    report_id: int
    assignee_id: int
    assigned_by_id: int
    assigned_at: datetime
    status: ReportStatusEnum
    specialty_id: int


class StatusChange(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: ReportStatusEnum
    comment: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def comment_required_for_exceptions(self) -> "StatusChange":
        if self.status in {ReportStatusEnum.BLOQUEADA, ReportStatusEnum.REABIERTA} and not self.comment:
            raise ValueError("El comentario es obligatorio para bloquear o reabrir")
        return self


class StatusEventRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: int
    report_id: int
    from_status: ReportStatusEnum
    to_status: ReportStatusEnum
    actor_id: int
    comment: Optional[str]
    created_at: datetime
