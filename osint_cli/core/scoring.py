"""Credibility scoring engine."""

from __future__ import annotations

from osint_cli.models.investigation import InvestigationReport


class ScoringEngine:
    """Weighted score computation for credibility."""

    def score(self, report: InvestigationReport) -> tuple[float, str, str]:
        """Return (score, confidence, explanation)."""
        score = 50.0
        explanations: list[str] = []

        if report.claim_analysis.emotional_language_score < 0.15:
            score += 8
            explanations.append("Low emotional language detected (+8).")
        else:
            score -= 8
            explanations.append("High emotional language detected (-8).")

        if len(report.claim_analysis.factual_components) >= 2:
            score += 10
            explanations.append("Multiple factual components identified (+10).")

        if report.earliest_source and report.earliest_source.date:
            score += 10
            explanations.append("Earliest source has identifiable date (+10).")

        if report.domain_intel:
            if (report.domain_intel.age_days or 0) > 365:
                score += 10
                explanations.append("Domain older than 1 year (+10).")
            if report.domain_intel.archive_snapshots_found:
                score += 6
                explanations.append("Archive snapshots found (+6).")
            if report.domain_intel.crt_issued:
                score += 4
                explanations.append("Certificate transparency history exists (+4).")

        if report.media_forensics:
            if report.media_forensics.duplicate_warning:
                score -= 12
                explanations.append("Potential duplicate image reuse detected (-12).")
            else:
                score += 4
                explanations.append("No duplicate image hash warning (+4).")

        if report.network_analysis:
            if report.network_analysis.node_count > 5:
                score -= 4
                explanations.append("Wide propagation may indicate amplification (-4).")
            if report.network_analysis.earliest_poster:
                score += 4
                explanations.append("Earliest poster identified (+4).")

        clamped = max(0.0, min(100.0, score))
        confidence = "LOW" if clamped < 40 else "MEDIUM" if clamped < 75 else "HIGH"
        return round(clamped, 2), confidence, " ".join(explanations)
