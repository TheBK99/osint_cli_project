"""Media forensics: EXIF extraction and perceptual hashing."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image
import imagehash

from osint_cli.models.investigation import MediaForensicsResult
from osint_cli.utils.helpers import load_json, save_json
from osint_cli.utils.logger import get_logger

logger = get_logger(__name__)

HASH_INDEX_PATH = Path("osint_cli/data/hash_index.json")


class MediaForensics:
    """Analyze image files for metadata and duplicate signals."""

    def analyze(self, image_path: str) -> MediaForensicsResult:
        """Run EXIF + pHash analysis."""
        path = Path(image_path)
        exif_data = self._extract_exif(path)
        perceptual_hash = self._compute_hash(path)
        duplicate_warning = self._update_hash_index(path, perceptual_hash)

        return MediaForensicsResult(
            file_path=str(path),
            exif=exif_data,
            perceptual_hash=perceptual_hash,
            duplicate_warning=duplicate_warning,
        )

    def _extract_exif(self, path: Path) -> dict[str, Any]:
        try:
            result = subprocess.run(
                ["exiftool", "-j", str(path)],
                check=True,
                capture_output=True,
                text=True,
            )
            parsed = json.loads(result.stdout)
            return parsed[0] if parsed else {}
        except Exception as exc:
            logger.info("exif_extraction_failed", file=str(path), error=str(exc))
            return {}

    def _compute_hash(self, path: Path) -> str | None:
        try:
            with Image.open(path) as image:
                return str(imagehash.phash(image))
        except Exception as exc:
            logger.info("image_hash_failed", file=str(path), error=str(exc))
            return None

    def _update_hash_index(self, path: Path, phash: str | None) -> bool:
        if not phash:
            return False
        index = load_json(HASH_INDEX_PATH)
        known: dict[str, str] = index.get("hashes", {})

        duplicate = phash in known and known[phash] != str(path)
        known[phash] = str(path)
        index["hashes"] = known
        save_json(HASH_INDEX_PATH, index)
        return duplicate
