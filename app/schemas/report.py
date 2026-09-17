from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.models.report import ReportPriorityEnum, ReportStatusEnum


class ReportUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    title: str
    description: str
    campus_id: int
    faculty_id: int
    location_id: int
    image_url: Optional[str] = None


class ReportCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    title: str
    description: str
    campus_id: int
    faculty_id: int
    location_id: int
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
    faculty_label: str
    space_label: str
    campus_id: Optional[int]
    faculty_id: Optional[int]
    location_id: Optional[int]
    status: ReportStatusEnum
    image_url: Optional[str]
    author_id: int
    author: ReportAuthor
    classified: bool
    priority: Optional[ReportPriorityEnum]
    awaiting_validation: bool
    created_at: datetime
    updated_at: datetime
