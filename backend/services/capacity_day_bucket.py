"""Capacity Stage 1 — DAY planning bucket helpers."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from services.resource_state_write_common import ResourceStateValidationError


def resolve_timezone(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError as exc:
        raise ResourceStateValidationError(
            "invalid_timezone", f"unknown timezone: {tz_name}"
        ) from exc


def day_bounds_for_date(bucket_date: date, tz_name: str) -> tuple[datetime, datetime]:
    """Inclusive start / exclusive end of calendar day in timezone."""
    tz = resolve_timezone(tz_name)
    start = datetime(bucket_date.year, bucket_date.month, bucket_date.day, tzinfo=tz)
    end = start + timedelta(days=1)
    return start, end


def _as_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def validate_day_bucket(
    bucket_start: datetime, bucket_end: datetime, tz_name: str
) -> date:
    """Require bucket_start/end to match exactly one DAY window in tz."""
    if bucket_end <= bucket_start:
        raise ResourceStateValidationError(
            "invalid_bucket", "bucket_end must be after bucket_start"
        )
    start = _as_aware(bucket_start)
    end = _as_aware(bucket_end)
    tz = resolve_timezone(tz_name)
    bucket_date = start.astimezone(tz).date()
    expected_start, expected_end = day_bounds_for_date(bucket_date, tz_name)
    if start.astimezone(timezone.utc) != expected_start.astimezone(
        timezone.utc
    ) or end.astimezone(timezone.utc) != expected_end.astimezone(timezone.utc):
        raise ResourceStateValidationError(
            "invalid_bucket",
            "Stage 1 requires exact DAY bucket bounds for the given timezone",
        )
    return bucket_date
