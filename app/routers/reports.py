from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import require_roles
from app.models.report import ReportPriorityEnum, ReportStatusEnum
from app.models.role import RoleEnum
from app.models.specialty import IncidentCategoryEnum
from app.schemas.reports import ReportSummary
from app.services import reports as reports_service

router = APIRouter(
    dependencies=[
        Depends(
            require_roles(
                RoleEnum.COORDINADOR,
                RoleEnum.RESPONSABLE_AREA,
                RoleEnum.ADMINISTRADOR,
            )
        )
    ]
)


@router.get("/summary", response_model=ReportSummary)
def summary(
    start_date: date | None = None,
    end_date: date | None = None,
    category_id: IncidentCategoryEnum | None = None,
    area_id: int | None = Query(default=None, gt=0),
    location_id: int | None = Query(default=None, gt=0),
    building_id: int | None = Query(default=None, gt=0),
    status: ReportStatusEnum | None = None,
    priority: ReportPriorityEnum | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ReportSummary:
    return reports_service.summary(
        db,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        area_id=area_id,
        location_id=location_id,
        building_id=building_id,
        report_status=status,
        priority=priority,
        limit=limit,
        offset=offset,
    )
