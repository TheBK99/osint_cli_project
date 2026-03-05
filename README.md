# OSINT CLI Project

A production-oriented local OSINT command-line toolkit for claim verification, source tracing, domain intelligence, media forensics, and propagation analysis.

## Installation

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
python -m playwright install chromium
python -m spacy download en_core_web_sm
```

Install `exiftool` using your package manager:

```bash
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install -y libimage-exiftool-perl
```

## CLI Usage

```bash
osint investigate --text "A satellite image proves event X happened yesterday"
osint investigate --url "https://example.com/news/article"
osint investigate --image ./evidence.jpg

osint domain example.com
osint media ./evidence.jpg
osint trace --keyword "event x eyewitness report"
osint export --format json
```

## Example Output (terminal)

```text
--------------------------------
CLAIM SUMMARY
- Source type: text
- Claim: A satellite image proves event X happened yesterday

ENTITIES
- event X

EARLIEST SOURCE
- 2025-01-05 | https://news.example.org/first-reference

TIMELINE TABLE
Date        URL                                         Title
2025-01-05  https://news.example.org/first-reference    First report
2025-01-06  https://blog.example.net/analysis           Follow-up

DOMAIN ANALYSIS
- Domain age days: 5135
- Archive snapshots: true

MEDIA FINDINGS
- EXIF keys: 23
- Perceptual hash: 81ff007e00ff00ff

PROPAGATION SUMMARY
- Earliest poster: @example_user
- Nodes: 18
- Edges: 17

FINAL SCORE
- Credibility score: 74.2 / 100
- Confidence level: MEDIUM
--------------------------------
```

## JSON Export

The `investigate` command stores the latest report at:

```text
osint_cli/data/latest_investigation.json
```

`osint export --format json` prints the structured report from the latest run.

## Troubleshooting (GitHub Workspace / Codespaces)

If `osint trace` logs Playwright launch errors like missing libraries (for example `libatk-1.0.so.0`), install the browser dependencies inside the workspace and retry:

```bash
sudo playwright install-deps chromium
python -m playwright install chromium
```

The tracer now includes a fallback HTTP fetch mode when a Playwright browser cannot start, but full browser scraping quality is best when dependencies are installed.
