"""Build map embed payloads from vinwonders_destinations_data.json."""

from __future__ import annotations

from typing import Any

from src.vinwonders.destinations_data import match_region


def _bbox_from_points(
    points: list[tuple[float, float]], padding: float = 0.04
) -> list[float]:
    lats = [p[0] for p in points]
    lngs = [p[1] for p in points]
    return [
        min(lngs) - padding,
        min(lats) - padding,
        max(lngs) + padding,
        max(lats) + padding,
    ]


def _osm_embed_url(
    bbox: list[float],
    *,
    marker_lat: float,
    marker_lng: float,
) -> str:
    min_lon, min_lat, max_lon, max_lat = bbox
    return (
        "https://www.openstreetmap.org/export/embed.html"
        f"?bbox={min_lon},{min_lat},{max_lon},{max_lat}&layer=mapnik"
        f"&marker={marker_lat}%2C{marker_lng}"
    )


def build_destination_map_payload(region_or_query: str) -> dict[str, Any] | None:
    """Map center, markers, and OSM embed URL from internal destination data."""
    region = match_region(region_or_query)
    if not region:
        return None

    map_meta = region.get("map") or {}
    center = map_meta.get("center") or {}
    center_lat = float(center.get("lat", 0))
    center_lng = float(center.get("lng", 0))
    if not center_lat and not center_lng:
        return None

    markers: list[dict[str, Any]] = []
    points: list[tuple[float, float]] = [(center_lat, center_lng)]
    for site in region.get("sub_locations") or []:
        lat, lng = site.get("lat"), site.get("lng")
        if lat is None or lng is None:
            continue
        lat_f, lng_f = float(lat), float(lng)
        points.append((lat_f, lng_f))
        markers.append(
            {
                "code": site.get("code", ""),
                "name": site.get("name", ""),
                "tag": site.get("tag", ""),
                "lat": lat_f,
                "lng": lng_f,
            }
        )

    bbox = map_meta.get("bbox")
    if not bbox or len(bbox) != 4:
        bbox = _bbox_from_points(points)

    embed_url = map_meta.get("embedUrl") or _osm_embed_url(
        bbox, marker_lat=center_lat, marker_lng=center_lng
    )

    return {
        "region": region.get("destination_name", ""),
        "destinationCode": region.get("destination_code", ""),
        "center": {"lat": center_lat, "lng": center_lng},
        "zoom": int(map_meta.get("zoom", 11)),
        "bbox": bbox,
        "embedUrl": embed_url,
        "markers": markers,
        "subLocationCount": len(markers),
    }
