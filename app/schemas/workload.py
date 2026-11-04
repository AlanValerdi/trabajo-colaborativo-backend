from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from app.schemas.report import ReportRead

class WorkloadCounts(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    total: int = 0
    pending: int = 0
    resolved: int = 0
    closed: int = 0
    by_status: dict[str, int] = Field(default_factory=dict)
    by_priority: dict[str, int] = Field(default_factory=dict)

class WorkloadGroup(WorkloadCounts):
    specialty_id: int | None = None
    specialty_name: str | None = None
    assignee_id: int | None = None
    assignee_name: str | None = None

class WorkloadSummary(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    summary: WorkloadCounts
    by_area: list[WorkloadGroup]
    by_technician: list[WorkloadGroup]
    by_area_and_technician: list[WorkloadGroup]

class WorkloadReports(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ReportRead]
