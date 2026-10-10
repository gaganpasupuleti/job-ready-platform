"""Calendar windows for when a listing entered JobReady.

`jobs.first_seen_at` is the portal ingestion timestamp. `jobs.posted_at` is the
external employer posting date and is not read here.

Portal dates use India Standard Time (UTC+05:30). India does not observe
daylight saving, so the offset is fixed. Presets and custom ranges are
calendar dates in that zone, not rolling hour counts.

Every window is half-open: the start instant is included and the end instant
is excluded.

- ``today`` is the current IST calendar day, ``[today 00:00, tomorrow 00:00)``.
- ``3d``, ``7d``, and ``30d`` include that current day plus the previous
  ``N - 1`` calendar days. Last 3 days is
  ``[today minus 2 days at 00:00, tomorrow 00:00)``.
- ``added_from`` and ``added_to`` are inclusive IST calendar dates. A range of
  1 October through 3 October is ``[1 Oct 00:00, 4 Oct 00:00)``. Either side
  may be omitted. A preset cannot be combined with a custom range.

A missing ``first_seen_at`` matches no portal-date filter. It is not treated
as an old listing. Current rows store the timestamp as non-null; the SQL
predicate still requires it so a null would stay out of these results and
would remain visible when no portal-date filter is selected.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone

PORTAL_UTC_OFFSET = timedelta(hours=5, minutes=30)
PORTAL_TZ = timezone(PORTAL_UTC_OFFSET)
ADDED_WITHIN_DAYS = {"today": 1, "3d": 3, "7d": 7, "30d": 30}


def _now() -> datetime:
    return datetime.now(UTC)


def portal_now(now: datetime | None = None) -> datetime:
    current = _now() if now is None else now
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    return current.astimezone(PORTAL_TZ)


def portal_day_start(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=PORTAL_TZ)


def added_window(
    added_within: str | None,
    added_from: date | None,
    added_to: date | None,
    *,
    now: datetime | None = None,
) -> tuple[datetime | None, datetime | None]:
    """Return ``[start, end)`` in IST, or ``(None, None)`` when unfiltered."""
    preset = (added_within or "").strip() or None
    if preset and (added_from is not None or added_to is not None):
        raise ValueError("use either added_within or an added_from/added_to range")
    if preset:
        days = ADDED_WITHIN_DAYS.get(preset)
        if days is None:
            raise ValueError("added_within must be today, 3d, 7d, or 30d")
        local_day = portal_now(now).date()
        start = portal_day_start(local_day - timedelta(days=days - 1))
        end = portal_day_start(local_day + timedelta(days=1))
        return start, end
    if added_from is None and added_to is None:
        return None, None
    if added_from is not None and added_to is not None and added_from > added_to:
        raise ValueError("added_from must be on or before added_to")
    start = portal_day_start(added_from) if added_from is not None else None
    end = portal_day_start(added_to + timedelta(days=1)) if added_to is not None else None
    return start, end
