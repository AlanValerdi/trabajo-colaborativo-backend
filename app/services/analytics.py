import csv
from datetime import datetime, timezone
from io import StringIO
from app.domain.attention import attention_times, utc
from app.models.report import ReportStatusEnum
from app.repositories import analytics as repository
from app.schemas.analytics import AnalyticsPage, AnalyticsRow, AnalyticsSummary, AreaSummary


def serialize(row, now):
    report = row.Report
    return AnalyticsRow(
        id=report.id, folio=report.folio, title=report.title, status=report.status,
        priority=report.priority, campus=report.campus_label,
        specialty_id=report.specialty_id, specialty=row.specialty or 'Sin área',
        assignee=row.assignee or 'Sin técnico', created_at=utc(report.created_at), rating=row.rating,
        **attention_times(report.created_at, report.status, row.started_at, row.resolved_at, row.closed_at, now),
    )


def page(db, filters, limit, offset):
    now = datetime.now(timezone.utc)
    return AnalyticsPage(items=[serialize(r, now) for r in repository.rows(db, filters, limit, offset)],
                         total=repository.count(db, filters), limit=limit, offset=offset)


def summary(db, filters):
    now = datetime.now(timezone.utc)
    statuses = {s.value: 0 for s in ReportStatusEnum}
    areas = {}
    totals = {key: [0.0, 0] for key in ('response_hours', 'resolution_hours', 'closure_hours', 'rating')}
    for raw in repository.rows(db, filters):
        row = serialize(raw, now)
        statuses[row.status.value] += 1
        area = areas.setdefault(row.specialty_id, AreaSummary(specialty_id=row.specialty_id, name=row.specialty))
        area.total += 1
        if row.status == ReportStatusEnum.RESUELTA:
            area.resolved += 1
        elif row.status == ReportStatusEnum.CERRADA:
            area.closed += 1
        else:
            area.pending += 1
        for key, accumulator in totals.items():
            value = getattr(row, key)
            if value is not None:
                accumulator[0] += value
                accumulator[1] += 1
    def average(key):
        total, count = totals[key]
        return round(total / count, 2) if count else None
    total = sum(statuses.values())
    return AnalyticsSummary(
        total=total, pending=total-statuses['resuelta']-statuses['cerrada'],
        resolved=statuses['resuelta'], closed=statuses['cerrada'], by_status=statuses,
        by_area=sorted(areas.values(), key=lambda a: (a.name, a.specialty_id or 0)),
        response_hours_average=average('response_hours'), response_sample=totals['response_hours'][1],
        resolution_hours_average=average('resolution_hours'), resolution_sample=totals['resolution_hours'][1],
        closure_hours_average=average('closure_hours'), closure_sample=totals['closure_hours'][1],
        rating_average=average('rating'), evaluation_count=totals['rating'][1], generated_at=now,
    )


def csv_cell(value):
    """Neutralize spreadsheet formulas, including whitespace-prefixed payloads."""
    if value is None:
        return ''
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


def export_csv(db, filters):
    now = datetime.now(timezone.utc)
    buffer = StringIO()
    writer = csv.writer(buffer)
    yield '\ufeff'  # UTF-8 BOM for Excel / accented Spanish text
    def line(values):
        buffer.seek(0)
        buffer.truncate(0)
        writer.writerow([csv_cell(value) for value in values])
        return buffer.getvalue()
    yield line(['Folio', 'Título', 'Estado', 'Prioridad', 'Campus', 'Área', 'Técnico',
                'Creación UTC', 'Respuesta (horas)', 'Resolución (horas)', 'Cierre (horas)',
                'Abierta (horas)', 'Evaluación (1-5)'])
    for raw in repository.rows(db, filters):
        row = serialize(raw, now)
        yield line([row.folio, row.title, row.status.value, row.priority.value if row.priority else '',
                    row.campus, row.specialty, row.assignee, row.created_at.isoformat(),
                    row.response_hours, row.resolution_hours, row.closure_hours, row.open_hours, row.rating])
