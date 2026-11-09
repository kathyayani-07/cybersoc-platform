from datetime import datetime, timezone


def utc_now_naive() -> datetime:
    """Return a naive UTC timestamp for SQLite's timezone-naive DateTime columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def as_utc_naive(value: datetime) -> datetime:
    """Normalize offset-aware input to naive UTC; treat legacy naive input as UTC."""
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def utc_isoformat(value: datetime | None) -> str | None:
    """Serialize a stored naive-UTC or aware datetime as an explicit UTC ISO value."""
    if value is None:
        return None
    normalized = as_utc_naive(value).replace(tzinfo=timezone.utc)
    return normalized.isoformat().replace("+00:00", "Z")
