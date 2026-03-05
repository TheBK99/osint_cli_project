"""Reusable helper functions."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def safe_iso_date(value: Any) -> str | None:
    """Convert several datetime-like values to an ISO date string."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, str):
        return value[:10]
    return str(value)


async def rate_limit_sleep(delay_seconds: float) -> None:
    """Apply rate limiting delay between network operations."""
    await asyncio.sleep(delay_seconds)


def ensure_parent_dir(path: Path) -> None:
    """Ensure parent directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, payload: dict[str, Any]) -> None:
    """Persist a JSON payload."""
    ensure_parent_dir(path)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    """Load JSON if available, otherwise return empty dict."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
