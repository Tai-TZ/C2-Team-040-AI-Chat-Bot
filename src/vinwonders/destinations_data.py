"""Load and match VinWonders destinations from internal JSON."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.utils.text import normalize_text

ROOT = Path(__file__).resolve().parents[2]
DESTINATIONS_PATH = ROOT / "vinwonders_destinations_data.json"


@lru_cache(maxsize=1)
def load_destinations() -> dict[str, Any]:
    return json.loads(DESTINATIONS_PATH.read_text(encoding="utf-8"))


def _region_score(query: str, region_name: str) -> int:
    q = normalize_text(query)
    rn = normalize_text(region_name)
    if not q or not rn:
        return 0
    if q == rn:
        return 100
    if q in rn or rn in q:
        return 80
    if any(tok in rn for tok in q.split() if len(tok) > 2):
        return 50
    return 0


def match_region(query: str) -> dict[str, Any] | None:
    """Best-matching destination region for a query or user message."""
    if not query.strip():
        return None
    best: tuple[int, dict[str, Any]] | None = None
    for region in load_destinations().get("destinations", []):
        name = region.get("destination_name", "")
        score = _region_score(query, name)
        if score > 0 and (best is None or score > best[0]):
            best = (score, region)
    return best[1] if best else None


def find_region_name_in_text(text: str) -> str | None:
    """Region name detected in free-form user input (bootstrap)."""
    region = match_region(text)
    return region.get("destination_name") if region else None


def destination_names() -> list[str]:
    return [
        r.get("destination_name", "")
        for r in load_destinations().get("destinations", [])
        if r.get("destination_name")
    ]
