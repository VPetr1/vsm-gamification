from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_aware(dt: datetime) -> datetime:
    """SQLite drops tzinfo on round-trip; Postgres keeps it. Treat naive values as UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def current_time() -> datetime:
    """FastAPI dependency: the single source of "now" per request. Tests override it."""
    return utcnow()
