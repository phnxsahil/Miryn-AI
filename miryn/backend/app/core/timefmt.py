"""Timestamp serialization helpers for API responses."""

import re
from datetime import datetime, timezone


def iso_with_utc(value):
    """Return an ISO-8601 timestamp carrying an explicit UTC offset.

    Timestamp columns are naive (``timestamp without time zone``) holding UTC
    wall time. Without an offset, browsers parse the serialized value as
    *local* time, so a chat updated just after local midnight but before
    UTC midnight was grouped under "Yesterday". Values that already carry an
    offset are left unchanged.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.isoformat()
    text_value = str(value)
    if text_value.endswith("Z") or re.search(r"[+-]\d{2}:?\d{2}$", text_value):
        return text_value
    return text_value + "Z"
