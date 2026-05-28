"""Environment-backed settings helpers."""

from __future__ import annotations

import os


def _get_str(name: str, default: str) -> str:
    """Get string setting from environment."""
    return os.getenv(name, default)


def _get_int(name: str, default: int) -> int:
    """Get integer setting from environment."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    """Get float setting from environment."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _get_bool(name: str, default: bool) -> bool:
    """Get boolean setting from environment."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

