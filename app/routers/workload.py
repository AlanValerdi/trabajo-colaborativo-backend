from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.dependencies.auth import require_roles
from app.models.role import RoleEnum
from app.models.report import ReportStatusEnum, ReportPriorityEnum
from app.schemas.workload import WorkloadSummary, WorkloadReports
from app.services import workload

router=APIRouter(dependencies=[Depends(require_roles(RoleEnum.COORDINADOR,RoleEnum.RESPONSABLE_AREA))])

@router.get('',response_model=WorkloadSummary)
def summary(specialty_id: int|None=Query(None,alias='specialtyId',gt=0),assignee_id: int|None=Query(None,alias='assigneeId',gt=0),db:Session=Depends(get_db)):
    return workload.summary(db,specialty_id,assignee_id)

@router.get('/reports',response_model=WorkloadReports)
def reports(specialty_id: int|None=Query(None,alias='specialtyId',gt=0),assignee_id: int|None=Query(None,alias='assigneeId',gt=0),status:ReportStatusEnum|None=None,priority:ReportPriorityEnum|None=None,pending_only:bool=Query(False,alias='pendingOnly'),limit:int=Query(50,ge=1,le=200),offset:int=Query(0,ge=0),db:Session=Depends(get_db)):
    return workload.reports(db,specialty_id,assignee_id,status,priority,pending_only,limit,offset)
