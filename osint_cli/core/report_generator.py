"""Render terminal and JSON outputs for investigations."""

from __future__ import annotations

import json
from pathlib import Path

from tabulate import tabulate

from osint_cli.models.investigation import InvestigationReport
from osint_cli.utils.helpers import save_json


class ReportGenerator:
    """Create structured and human-readable reports."""

    def terminal_report(self, report: InvestigationReport) -> str:
        """Generate formatted terminal report."""
        timeline_table = [
            [item.date or "N/A", item.url, item.title]
            for item in report.timeline[:10]
        ]
        timeline_render = tabulate(timeline_table, headers=["Date", "URL", "Title"], tablefmt="github")

        domain_lines = "N/A"
        if report.domain_intel:
            domain_lines = (
                f"- Domain: {report.domain_intel.domain}\n"
                f"- Domain age days: {report.domain_intel.age_days}\n"
                f"- Registrar: {report.domain_intel.registrar}\n"
                f"- Archive snapshots: {report.domain_intel.archive_snapshots_found}\n"
                f"- DNS record types: {', '.join(report.domain_intel.dns_records.keys())}"
            )

        media_lines = "N/A"
        if report.media_forensics:
            media_lines = (
                f"- EXIF keys: {len(report.media_forensics.exif)}\n"
                f"- Perceptual hash: {report.media_forensics.perceptual_hash}\n"
                f"- Duplicate warning: {report.media_forensics.duplicate_warning}"
            )

        propagation_lines = "N/A"
        if report.network_analysis:
            propagation_lines = (
                f"- Earliest poster: {report.network_analysis.earliest_poster}\n"
                f"- Nodes: {report.network_analysis.node_count}\n"
                f"- Edges: {report.network_analysis.edge_count}\n"
                f"- Top nodes: {report.network_analysis.top_degree_nodes}"
            )

        earliest_source = "N/A"
        if report.earliest_source:
            earliest_source = f"{report.earliest_source.date or 'N/A'} | {report.earliest_source.url}"

        return (
            "--------------------------------\n"
            "CLAIM SUMMARY\n"
            f"- Source type: {report.input_type}\n"
            f"- Claim: {report.claim_input}\n\n"
            "ENTITIES\n"
            + "\n".join([f"- {e}" for e in report.claim_analysis.entities] or ["- None detected"])
            + "\n\n"
            "EARLIEST SOURCE\n"
            f"- {earliest_source}\n\n"
            "TIMELINE TABLE\n"
            f"{timeline_render}\n\n"
            "DOMAIN ANALYSIS\n"
            f"{domain_lines}\n\n"
            "MEDIA FINDINGS\n"
            f"{media_lines}\n\n"
            "PROPAGATION SUMMARY\n"
            f"{propagation_lines}\n\n"
            "FINAL SCORE\n"
            f"- Credibility score: {report.credibility_score} / 100\n"
            f"- Confidence level: {report.confidence_level}\n"
            f"- Explanation: {report.score_explanation}\n"
            "--------------------------------"
        )

    def save_json_report(self, report: InvestigationReport, path: Path) -> None:
        """Persist report as structured JSON."""
        save_json(path, report.to_dict())

    def format_json(self, report: InvestigationReport) -> str:
        """Return pretty JSON string."""
        return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
