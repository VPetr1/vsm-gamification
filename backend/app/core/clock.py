from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(dt: datetime) -> datetime:
    """Normalise DB timestamps to UTC: SQLite returns naive values, Postgres the session's zone."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def current_time() -> datetime:
    """FastAPI dependency: the single source of "now" per request. Tests override it."""
    return utcnow()
