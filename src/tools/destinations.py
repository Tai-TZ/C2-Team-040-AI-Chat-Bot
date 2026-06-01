"""Destination lookup tools for the VinWonders agent."""

from __future__ import annotations

import json
from typing import Any

from src.utils.text import normalize_text
from src.vinwonders.destinations_data import load_destinations


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


def _site_score(query: str, region_name: str, site_name: str) -> int:
    q = normalize_text(query)
    rn = normalize_text(region_name)
    sn = normalize_text(site_name)
    if q == rn or q == sn:
        return 100
    if q in rn or rn in q:
        return 80
    if q in sn or sn in q:
        return 70
    if any(tok in rn for tok in q.split() if len(tok) > 2):
        return 50
    return 0


def list_destinations(region_query: str = "") -> str:
    """List VinWonders regions and site codes (optional filter)."""
    q = normalize_text(region_query) if region_query else ""
    rows: list[dict[str, str]] = []

    for region in load_destinations().get("destinations", []):
        name = region.get("destination_name", "")
        if q and q not in normalize_text(name):
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
    if not normalize_text(query):
        return json.dumps({"error": "query is required"}, ensure_ascii=False)

    best: tuple[int, dict[str, Any], dict[str, Any]] | None = None

    for region in load_destinations().get("destinations", []):
        region_name = region.get("destination_name", "")
        for site in region.get("sub_locations", []):
            score = _site_score(query, region_name, site.get("name", ""))
            if score > 0 and (best is None or score > best[0]):
                best = (score, region, site)

    if best is None:
        return json.dumps(
            {"error": f"Không tìm thấy địa điểm khớp '{query}'"},
            ensure_ascii=False,
        )

    _, region, site = best
    primary = _primary_site(region)
    attractions = [
        {
            "code": s.get("code", ""),
            "name": s.get("name", ""),
            "tag": s.get("tag", ""),
        }
        for s in region.get("sub_locations") or []
    ]
    return json.dumps(
        {
            "query": query,
            "region": region.get("destination_name"),
            "supplierCode": site.get("code"),
            "siteName": site.get("name"),
            "tag": site.get("tag"),
            "primaryVinWondersCode": primary.get("code"),
            "primaryVinWondersName": primary.get("name"),
            "attractions": attractions,
            "subLocationCount": len(attractions),
        },
        ensure_ascii=False,
    )
