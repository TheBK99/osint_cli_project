"""Configuration objects and constants for the OSINT CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Application runtime configuration."""

    user_agent: str = "osint-cli/0.1 (+local investigation tool)"
    request_timeout_seconds: float = 15.0
    max_concurrent_requests: int = 5
    rate_limit_seconds: float = 1.0
    playwright_timeout_ms: int = 15000
    latest_report_path: Path = Path("osint_cli/data/latest_investigation.json")


CONFIG = AppConfig()
