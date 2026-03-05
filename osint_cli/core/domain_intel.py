"""Domain intelligence module (WHOIS, DNS, certificate transparency, archive)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import dns.resolver
import httpx
import whois

from osint_cli.config import CONFIG
from osint_cli.models.investigation import DomainIntelResult
from osint_cli.utils.helpers import rate_limit_sleep, safe_iso_date
from osint_cli.utils.logger import get_logger

logger = get_logger(__name__)


class DomainIntel:
    """Perform domain intelligence checks using open sources."""

    RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT"]

    async def analyze(self, domain: str) -> DomainIntelResult:
        """Collect domain intelligence artifacts."""
        dns_records = self._lookup_dns(domain)
        whois_age, registrar = self._lookup_whois(domain)
        crt_issued = await self._crt_search(domain)
        archive_snapshots = await self._archive_available(domain)

        return DomainIntelResult(
            domain=domain,
            age_days=whois_age,
            registrar=registrar,
            dns_records=dns_records,
            crt_issued=crt_issued,
            archive_snapshots_found=archive_snapshots,
        )

    def _lookup_dns(self, domain: str) -> dict[str, list[str]]:
        records: dict[str, list[str]] = {}
        resolver = dns.resolver.Resolver()
        for record_type in self.RECORD_TYPES:
            try:
                answers = resolver.resolve(domain, record_type)
                records[record_type] = [str(r) for r in answers]
            except Exception as exc:
                logger.info("dns_lookup_failed", domain=domain, record_type=record_type, error=str(exc))
                records[record_type] = []
        return records

    def _lookup_whois(self, domain: str) -> tuple[int | None, str | None]:
        try:
            info: dict[str, Any] = whois.whois(domain)
            creation_date = info.get("creation_date")
            if isinstance(creation_date, list) and creation_date:
                creation_date = creation_date[0]
            registrar = info.get("registrar")
            if isinstance(registrar, list):
                registrar = registrar[0]
            if isinstance(creation_date, datetime):
                now = datetime.now(timezone.utc)
                if creation_date.tzinfo is None:
                    creation_date = creation_date.replace(tzinfo=timezone.utc)
                age_days = (now - creation_date).days
                return age_days, str(registrar) if registrar else None
        except Exception as exc:
            logger.info("whois_lookup_failed", domain=domain, error=str(exc))
        return None, None

    async def _crt_search(self, domain: str) -> list[str]:
        url = f"https://crt.sh/?q={quote(domain)}&output=json"
        headers = {"User-Agent": CONFIG.user_agent}
        issued_dates: list[str] = []
        try:
            async with httpx.AsyncClient(timeout=CONFIG.request_timeout_seconds, headers=headers) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                for row in data[:20]:
                    date_str = safe_iso_date(row.get("entry_timestamp"))
                    if date_str:
                        issued_dates.append(date_str)
        except Exception as exc:
            logger.info("crt_search_failed", domain=domain, error=str(exc))
        await rate_limit_sleep(CONFIG.rate_limit_seconds)
        return sorted(set(issued_dates))

    async def _archive_available(self, domain: str) -> bool:
        url = (
            "https://web.archive.org/cdx/search/cdx"
            f"?url={quote(domain)}&output=json&fl=timestamp,original&limit=1"
        )
        headers = {"User-Agent": CONFIG.user_agent}
        try:
            async with httpx.AsyncClient(timeout=CONFIG.request_timeout_seconds, headers=headers) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                return len(data) > 1
        except Exception as exc:
            logger.info("archive_lookup_failed", domain=domain, error=str(exc))
            return False
