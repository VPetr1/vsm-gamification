from datetime import datetime, timedelta, timezone

from app.core.clock import as_utc


def test_as_utc_converts_zoned_and_naive_values():
    msk = timezone(timedelta(hours=3))
    assert as_utc(datetime(2026, 9, 25, 18, 0, tzinfo=msk)) == datetime(2026, 9, 25, 15, 0, tzinfo=timezone.utc)
    assert as_utc(datetime(2026, 9, 25, 18, 0, tzinfo=msk)).utcoffset() == timedelta(0)
    assert as_utc(datetime(2026, 9, 25, 15, 0)).tzinfo == timezone.utc
