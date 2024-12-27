"""Date and time utility functions."""

from datetime import datetime
from pytz import UTC


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)
