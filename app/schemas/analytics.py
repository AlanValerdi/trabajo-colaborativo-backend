from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.models.report import ReportPriorityEnum, ReportStatusEnum
from app.domain.attention import utc


class AnalyticsFilters(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    campus_id: int | None = Field(None, gt=0)
    specialty_id: int | None = Field(None, gt=0)
    assignee_id: int | None = Field(None, gt=0)
    status: ReportStatusEnum | None = None
    priority: ReportPriorityEnum | None = None

    @model_validator(mode='after')
    def valid_period(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError('La fecha inicial debe ser anterior o igual a la final')
        if self.end_date == date.max:
            raise ValueError('Fecha final fuera de rango')
        return self


class AttentionTimes(BaseModel):
    response_hours: float | None = None
    resolution_hours: float | None = None
    closure_hours: float | None = None
    open_hours: float | None = None


class AnalyticsPageFilters(AnalyticsFilters):
    limit: int = Field(25, ge=1, le=200)
    offset: int = Field(0, ge=0)


class AnalyticsRow(AttentionTimes):
    id: int
    folio: str
    title: str
    status: ReportStatusEnum
    priority: ReportPriorityEnum | None
    campus: str
    specialty_id: int | None
    specialty: str
    assignee: str
    created_at: datetime
    rating: int | None


class AnalyticsPage(BaseModel):
    items: list[AnalyticsRow]
    total: int
    limit: int
    offset: int


class AreaSummary(BaseModel):
    specialty_id: int | None
    name: str
    total: int = 0
    pending: int = 0
    resolved: int = 0
    closed: int = 0


class AnalyticsSummary(BaseModel):
    total: int
    pending: int
    resolved: int
    closed: int
    by_status: dict[str, int]
    by_area: list[AreaSummary]
    response_hours_average: float | None
    response_sample: int
    resolution_hours_average: float | None
    resolution_sample: int
    closure_hours_average: float | None
    closure_sample: int
    rating_average: float | None
    evaluation_count: int
    generated_at: datetime


class EvaluationCreate(BaseModel):
    rating: int = Field(ge=1, le=5, strict=True)
    comment: str | None = Field(None, max_length=1000)

    @field_validator('comment')
    @classmethod
    def clean_comment(cls, value):
        return value.strip() or None if value is not None else None


class EvaluationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    report_id: int
    author_id: int
    rating: int
    comment: str | None
    created_at: datetime

    @field_validator('created_at')
    @classmethod
    def utc_timestamp(cls, value):
        return utc(value)
