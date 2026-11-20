"""Attention metrics: elapsed calendar hours, always interpreted as UTC."""
from datetime import datetime, timezone


def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def elapsed_hours(start: datetime, end: datetime | None) -> float | None:
    if end is None or utc(end) < utc(start):
        return None
    return round((utc(end) - utc(start)).total_seconds() / 3600, 4)


def attention_times(created_at, status, started_at, resolved_at, closed_at, now):
    """Reopened incidents have no final duration until resolved again.

    Response is the first entry into en_progreso. Resolution/closure use the
    latest matching event, measured from creation, including blocked time.
    Missing historical events remain unknown rather than becoming zero.
    """
    terminal = status in ('resuelta', 'cerrada')
    return {
        'response_hours': elapsed_hours(created_at, started_at),
        'resolution_hours': elapsed_hours(created_at, resolved_at) if terminal else None,
        'closure_hours': elapsed_hours(created_at, closed_at) if status == 'cerrada' else None,
        'open_hours': None if terminal else elapsed_hours(created_at, now),
    }
