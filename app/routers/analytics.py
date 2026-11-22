from typing import Annotated
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.user import User
from app.schemas.analytics import (AnalyticsFilters, AnalyticsPageFilters, AnalyticsPage, AnalyticsSummary,
                                   AttentionTimes, EvaluationCreate, EvaluationRead)
from app.services import analytics, attention

router = APIRouter(dependencies=[Depends(require_roles(*attention.MANAGEMENT_ROLES))])
attention_router = APIRouter()
Database = Annotated[Session, Depends(get_db)]
Actor = Annotated[User, Depends(get_current_user)]
Filters = Annotated[AnalyticsFilters, Query()]


@router.get('/summary', response_model=AnalyticsSummary)
def summary(filters: Filters, db: Database):
    return analytics.summary(db, filters)


@router.get('/reports', response_model=AnalyticsPage)
def reports(filters: Annotated[AnalyticsPageFilters, Query()], db: Database):
    return analytics.page(db, filters, filters.limit, filters.offset)


@router.get('/export')
def export(filters: Filters, db: Database):
    return StreamingResponse(analytics.export_csv(db, filters), media_type='text/csv; charset=utf-8',
                             headers={'Content-Disposition': 'attachment; filename="reporte-atencion.csv"',
                                      'Cache-Control': 'no-store'})


@attention_router.get('/{folio}/attention-times', response_model=AttentionTimes)
def attention_times(folio: str, db: Database, user: Actor):
    return attention.timings(db, folio, user)


@attention_router.get('/{folio}/evaluation', response_model=EvaluationRead | None)
def evaluation(folio: str, db: Database, user: Actor):
    return attention.evaluation(db, folio, user)


@attention_router.post('/{folio}/evaluation', response_model=EvaluationRead, status_code=201)
def create_evaluation(folio: str, data: EvaluationCreate, db: Database, user: Actor):
    return attention.create_evaluation(db, folio, user, data)
