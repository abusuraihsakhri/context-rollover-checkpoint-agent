"""Parsing helpers shared by command-line entry points."""
from typing import Any

_TRUE_VALUES = {"1", "true", "yes", "y", "on"}
_FALSE_VALUES = {"0", "false", "no", "n", "off", ""}


def parse_bool(value: Any) -> bool:
    """Parse common boolean representations without truthy-string surprises."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    normalized = str(value).strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(f"invalid boolean value: {value!r}")
