"""Destination lookup tools for the VinWonders agent."""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DESTINATIONS_FILE = ROOT / "vinwonders_destinations_data.json"


def _load() -> dict[str, Any]:
    return json.loads(DESTINATIONS_FILE.read_text(encoding="utf-8"))


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def _primary_site(region: dict[str, Any]) -> dict[str, Any]:
    sites = region.get("sub_locations") or []
    if not sites:
        raise ValueError("No sites in region")
    for site in sites:
        name = (site.get("name") or "").lower()
        code = (site.get("code") or "").upper()
        if "vinwonders" in name or code.endswith("VW1"):
            return site
    return sites[0]


def list_destinations(region_query: str = "") -> str:
    """List VinWonders regions and site codes (optional filter)."""
    data = _load()
    q = _normalize(region_query) if region_query else ""
    rows: list[dict[str, str]] = []

    for region in data.get("destinations", []):
        name = region.get("destination_name", "")
        if q and q not in _normalize(name):
            continue
        for site in region.get("sub_locations", []):
            rows.append(
                {
                    "region": name,
                    "siteName": site.get("name", ""),
                    "supplierCode": site.get("code", ""),
                    "tag": site.get("tag", ""),
                }
            )

    return json.dumps({"count": len(rows), "sites": rows}, ensure_ascii=False)


def resolve_site(query: str) -> str:
    """Resolve a place name to supplier_code (fuzzy match)."""
    q = _normalize(query)
    if not q:
        return json.dumps({"error": "query is required"}, ensure_ascii=False)

    data = _load()
    best: tuple[int, dict[str, Any], dict[str, Any]] | None = None

    for region in data.get("destinations", []):
        region_name = region.get("destination_name", "")
        rn = _normalize(region_name)
        for site in region.get("sub_locations", []):
            site_name = site.get("name", "")
            sn = _normalize(site_name)
            score = 0
            if q == rn or q == sn:
                score = 100
            elif q in rn or rn in q:
                score = 80
            elif q in sn or sn in q:
                score = 70
            elif any(tok in rn for tok in q.split() if len(tok) > 2):
                score = 50
            if score > 0 and (best is None or score > best[0]):
                best = (score, region, site)

    if best is None:
        return json.dumps(
            {"error": f"Không tìm thấy địa điểm khớp '{query}'"},
            ensure_ascii=False,
        )

    _, region, site = best
    primary = _primary_site(region)
    return json.dumps(
        {
            "query": query,
            "region": region.get("destination_name"),
            "supplierCode": site.get("code"),
            "siteName": site.get("name"),
            "tag": site.get("tag"),
            "primaryVinWondersCode": primary.get("code"),
            "primaryVinWondersName": primary.get("name"),
        },
        ensure_ascii=False,
    )
