from sqlalchemy import func
from sqlmodel import select
from app.models.report import Report, ReportStatusEnum, ReportPriorityEnum
from app.models.specialty import Specialty
from app.models.user import User
from app.models.user_role import UserRole
from app.models.role import RoleEnum
from app.schemas.workload import WorkloadCounts, WorkloadGroup, WorkloadSummary, WorkloadReports
from app.services.report import serialize_report


def filtered(specialty_id=None, assignee_id=None):
    clauses=[]
    if specialty_id is not None: clauses.append(Report.specialty_id == specialty_id)
    if assignee_id is not None: clauses.append(Report.assignee_id == assignee_id)
    return clauses


def counts(**kw):
    return WorkloadGroup(by_status={s.value:0 for s in ReportStatusEnum}, by_priority={**{p.value:0 for p in ReportPriorityEnum},'unclassified':0}, **kw)


def summary(db, specialty_id=None, assignee_id=None):
    areas={s.id:s.name for s in db.scalars(select(Specialty)).all()}
    users={u.id:u.name for u in db.scalars(select(User)).all()}
    area_groups={}
    tech_groups={}
    pairs={}
    for sid,name in areas.items():
        if specialty_id is None or sid==specialty_id:
            area_groups[sid]=counts(specialty_id=sid,specialty_name=name)
    active=db.scalars(select(User).join(UserRole).where(User.is_active == True,UserRole.role==RoleEnum.TECNICO)).all()
    for u in active:
        if assignee_id is None or u.id==assignee_id:
            tech_groups[u.id]=counts(assignee_id=u.id,assignee_name=u.name)
    total=counts()
    rows=db.execute(select(Report.specialty_id,Report.assignee_id,Report.status,Report.priority,func.count()).where(*filtered(specialty_id,assignee_id)).group_by(Report.specialty_id,Report.assignee_id,Report.status,Report.priority)).all()
    for sid,uid,status,priority,n in rows:
        area=area_groups.setdefault(sid,counts(specialty_id=sid,specialty_name=areas.get(sid,'Sin área')))
        tech=tech_groups.setdefault(uid,counts(assignee_id=uid,assignee_name=users.get(uid,'Sin técnico')))
        pair=pairs.setdefault((sid,uid),counts(specialty_id=sid,specialty_name=areas.get(sid,'Sin área'),assignee_id=uid,assignee_name=users.get(uid,'Sin técnico')))
        for group in [total,area,tech,pair]:
            group.total+=n
            group.by_status[status.value]+=n
            group.by_priority[priority.value if priority else 'unclassified']+=n
            if status==ReportStatusEnum.RESUELTA: group.resolved+=n
            elif status==ReportStatusEnum.CERRADA: group.closed+=n
            else: group.pending+=n
    return WorkloadSummary(summary=WorkloadCounts(**total.model_dump()),by_area=list(area_groups.values()),by_technician=list(tech_groups.values()),by_area_and_technician=list(pairs.values()))


def reports(db,specialty_id=None,assignee_id=None,status=None,priority=None,pending_only=False,limit=50,offset=0):
    clauses=filtered(specialty_id,assignee_id)
    if status is not None: clauses.append(Report.status==status)
    if priority is not None: clauses.append(Report.priority==priority)
    if pending_only: clauses.append(Report.status.not_in([ReportStatusEnum.RESUELTA,ReportStatusEnum.CERRADA]))
    total=db.scalar(select(func.count()).select_from(Report).where(*clauses))
    rows=db.scalars(select(Report).where(*clauses).order_by(Report.created_at.desc(),Report.id.desc()).offset(offset).limit(limit)).all()
    authors={u.id:u for u in db.scalars(select(User).where(User.id.in_({r.author_id for r in rows}))).all()}
    return WorkloadReports(total=total,limit=limit,offset=offset,items=[serialize_report(r,authors.get(r.author_id)) for r in rows])
