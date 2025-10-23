"""
DateTime utility functions for consistent UTC handling
"""
from datetime import datetime
from typing import Optional


def to_utc_isoformat(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert a datetime to ISO format with UTC timezone indicator.

    Args:
        dt: Datetime object (can be naive UTC datetime from datetime.utcnow())

    Returns:
        ISO format string with 'Z' suffix to indicate UTC, or None if dt is None

    Example:
        >>> to_utc_isoformat(datetime(2025, 1, 22, 10, 30, 45))
        '2025-01-22T10:30:45Z'
    """
    if dt is None:
        return None

    # Remove microseconds for cleaner output and add 'Z' to indicate UTC
    return dt.replace(microsecond=0).isoformat() + 'Z'


def to_utc_isoformat_with_ms(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert a datetime to ISO format with microseconds and UTC timezone indicator.

    Args:
        dt: Datetime object (can be naive UTC datetime from datetime.utcnow())

    Returns:
        ISO format string with 'Z' suffix to indicate UTC, or None if dt is None

    Example:
        >>> to_utc_isoformat_with_ms(datetime(2025, 1, 22, 10, 30, 45, 123456))
        '2025-01-22T10:30:45.123456Z'
    """
    if dt is None:
        return None

    # Keep microseconds and add 'Z' to indicate UTC
    return dt.isoformat() + 'Z'
