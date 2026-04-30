"""
Competition countdown state.

Stored in-process. On restart the value resets to the default.
Use the /api/countdown endpoints to adjust it at runtime.
"""

from datetime import datetime, timedelta

_countdown_end = datetime(2027, 8, 7, 19, 48, 35)


def get_end() -> datetime:
    return _countdown_end


def set_end(dt: datetime) -> None:
    global _countdown_end
    _countdown_end = dt


def add_minutes(minutes: int) -> datetime:
    global _countdown_end
    _countdown_end = datetime.now() + timedelta(minutes=minutes)
    return _countdown_end


def is_active() -> bool:
    """Return True while the competition is still running."""
    return datetime.now() <= _countdown_end
