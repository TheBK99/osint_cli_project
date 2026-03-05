"""Claim analysis using spaCy NLP."""

from __future__ import annotations

import re

import spacy
from spacy.language import Language

from osint_cli.models.investigation import ClaimAnalysisResult

EMOTIONAL_TERMS = {
    "shocking",
    "outrageous",
    "terrifying",
    "disaster",
    "horrific",
    "urgent",
    "panic",
    "heartbreaking",
}


class ClaimAnalyzer:
    """Analyze a claim text for entities, emotion, and factual components."""

    def __init__(self) -> None:
        self.nlp = self._load_model()

    @staticmethod
    def _load_model() -> Language:
        try:
            return spacy.load("en_core_web_sm")
        except Exception:
            return spacy.blank("en")

    def analyze(self, text: str) -> ClaimAnalysisResult:
        """Perform NLP analysis of claim text."""
        doc = self.nlp(text)
        entities = sorted({ent.text for ent in doc.ents if ent.text.strip()})

        lowered = text.lower()
        emotional_hits = sum(1 for word in EMOTIONAL_TERMS if word in lowered)
        token_count = max(1, len([t for t in re.split(r"\W+", lowered) if t]))
        emotional_score = min(1.0, emotional_hits / token_count * 10)

        factual_components: list[str] = []
        for sent in doc.sents if doc.has_annotation("SENT_START") else []:
            sentence = sent.text.strip()
            if re.search(r"\d", sentence) or any(k in sentence.lower() for k in ["according", "report", "study", "confirmed"]):
                factual_components.append(sentence)

        if not factual_components and text.strip():
            factual_components.append(text.strip())

        return ClaimAnalysisResult(
            entities=entities,
            emotional_language_score=round(emotional_score, 3),
            factual_components=factual_components,
        )
