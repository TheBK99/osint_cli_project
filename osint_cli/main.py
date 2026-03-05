"""Typer CLI entrypoint for OSINT workflows."""

from __future__ import annotations

import asyncio
from pathlib import Path
from urllib.parse import urlparse

import httpx
import typer
from bs4 import BeautifulSoup

from osint_cli.config import CONFIG
from osint_cli.core.claim_analyzer import ClaimAnalyzer
from osint_cli.core.domain_intel import DomainIntel
from osint_cli.core.media_forensics import MediaForensics
from osint_cli.core.network_analysis import NetworkAnalyzer
from osint_cli.core.report_generator import ReportGenerator
from osint_cli.core.scoring import ScoringEngine
from osint_cli.core.timeline_tracer import TimelineTracer
from osint_cli.models.investigation import InvestigationReport
from osint_cli.utils.helpers import load_json
from osint_cli.utils.logger import configure_logging, get_logger

app = typer.Typer(help="Local OSINT CLI for claim investigations")
logger = get_logger(__name__)


def _extract_domain(url: str) -> str | None:
    parsed = urlparse(url)
    return parsed.netloc or None


async def _fetch_url_text(url: str) -> str:
    headers = {"User-Agent": CONFIG.user_agent}
    async with httpx.AsyncClient(timeout=CONFIG.request_timeout_seconds, headers=headers, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        article = " ".join(tag.get_text(" ", strip=True) for tag in soup.select("p")[:15])
        return article or soup.get_text(" ", strip=True)[:1000]


async def _run_investigation(text: str | None, url: str | None, image: str | None) -> InvestigationReport:
    claim_analyzer = ClaimAnalyzer()
    tracer = TimelineTracer()
    domain_intel = DomainIntel()
    media = MediaForensics()
    network = NetworkAnalyzer()
    scorer = ScoringEngine()

    input_type = "text"
    claim_input = text or ""

    if url:
        input_type = "url"
        claim_input = await _fetch_url_text(url)
    elif image:
        input_type = "image"
        claim_input = f"Image investigation for {image}"

    claim = claim_analyzer.analyze(claim_input)
    trace_keyword = " ".join(claim.entities[:5]) if claim.entities else claim_input[:120]
    timeline = await tracer.trace(trace_keyword)
    earliest = timeline[0] if timeline else None

    domain_result = None
    domain = _extract_domain(url) if url else None
    if domain:
        domain_result = await domain_intel.analyze(domain)

    media_result = media.analyze(image) if image else None
    network_result = network.analyze_keyword(trace_keyword) if trace_keyword.strip() else None

    report = InvestigationReport(
        claim_input=claim_input,
        input_type=input_type,
        claim_analysis=claim,
        timeline=timeline,
        earliest_source=earliest,
        domain_intel=domain_result,
        media_forensics=media_result,
        network_analysis=network_result,
    )
    score, confidence, explanation = scorer.score(report)
    report.credibility_score = score
    report.confidence_level = confidence
    report.score_explanation = explanation
    return report


@app.callback()
def _callback() -> None:
    """Initialize logging once for all commands."""
    configure_logging()


@app.command()
def investigate(
    text: str | None = typer.Option(None, "--text", help="Claim text to investigate"),
    url: str | None = typer.Option(None, "--url", help="URL containing the claim"),
    image: str | None = typer.Option(None, "--image", help="Image path for media forensics"),
) -> None:
    """Run end-to-end investigation workflow."""
    if not any([text, url, image]):
        raise typer.BadParameter("Provide one input: --text, --url, or --image")

    report = asyncio.run(_run_investigation(text=text, url=url, image=image))
    renderer = ReportGenerator()
    renderer.save_json_report(report, CONFIG.latest_report_path)
    typer.echo(renderer.terminal_report(report))
    typer.echo("\nStructured JSON:\n")
    typer.echo(renderer.format_json(report))


@app.command()
def domain(target: str) -> None:
    """Run standalone domain intelligence analysis."""
    result = asyncio.run(DomainIntel().analyze(target))
    typer.echo(result)


@app.command()
def media(image_path: str) -> None:
    """Run standalone media forensics."""
    result = MediaForensics().analyze(image_path)
    typer.echo(result)


@app.command()
def trace(keyword: str = typer.Option(..., "--keyword", help="Keywords for source tracing")) -> None:
    """Trace earliest references for a keyword."""
    timeline = asyncio.run(TimelineTracer().trace(keyword))
    if not timeline:
        typer.echo("No timeline entries found.")
        return
    for item in timeline:
        typer.echo(f"{item.date or 'N/A'} | {item.url} | {item.title}")


@app.command()
def export(format: str = typer.Option("json", "--format", help="Export format")) -> None:
    """Export latest investigation report."""
    if format.lower() != "json":
        raise typer.BadParameter("Only --format json is currently supported")
    payload = load_json(CONFIG.latest_report_path)
    if not payload:
        typer.echo("No investigation data found. Run `osint investigate` first.")
        raise typer.Exit(code=1)
    typer.echo_json(payload)


if __name__ == "__main__":
    app()
