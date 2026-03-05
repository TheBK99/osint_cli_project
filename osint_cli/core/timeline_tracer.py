"""Timeline tracing using Playwright scraping and chronological sorting."""

from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from osint_cli.config import CONFIG
from osint_cli.models.investigation import TimelineEntry
from osint_cli.utils.helpers import rate_limit_sleep
from osint_cli.utils.logger import get_logger

logger = get_logger(__name__)

DATE_PATTERNS = [
    r"(\d{4}-\d{2}-\d{2})",
    r"([A-Z][a-z]{2,8}\s+\d{1,2},\s+\d{4})",
]


class TimelineTracer:
    """Trace earliest indexed references for a keyword/claim."""

    async def trace(self, keyword: str, max_results: int = 20) -> list[TimelineEntry]:
        """Scrape search results and return sorted timeline entries."""
        query_url = f"https://duckduckgo.com/html/?q={quote_plus(keyword)}"
        html = await self._scrape_page(query_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        entries: list[TimelineEntry] = []

        for result in soup.select(".result")[:max_results]:
            title_tag = result.select_one(".result__a")
            snippet_tag = result.select_one(".result__snippet")
            if not title_tag:
                continue
            url = title_tag.get("href", "")
            title = title_tag.get_text(strip=True)
            snippet = snippet_tag.get_text(" ", strip=True) if snippet_tag else ""
            date_value = self._extract_date(snippet)
            entries.append(TimelineEntry(url=url, title=title, date=date_value))

        entries.sort(key=lambda e: self._sort_key(e.date))
        return entries

    async def _scrape_page(self, url: str) -> str:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(user_agent=CONFIG.user_agent)
                await page.goto(url, wait_until="domcontentloaded", timeout=CONFIG.playwright_timeout_ms)
                await rate_limit_sleep(CONFIG.rate_limit_seconds)
                content = await page.content()
                await browser.close()
                return content
        except Exception as exc:
            logger.info("timeline_scrape_failed", url=url, error=str(exc))
            return ""

    @staticmethod
    def _extract_date(text: str) -> str | None:
        for pattern in DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                raw = match.group(1)
                for fmt in ["%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"]:
                    try:
                        return datetime.strptime(raw, fmt).date().isoformat()
                    except ValueError:
                        continue
                if re.match(r"\d{4}-\d{2}-\d{2}", raw):
                    return raw
        return None

    @staticmethod
    def _sort_key(value: str | None) -> tuple[int, str]:
        if value:
            return (0, value)
        return (1, "9999-12-31")
