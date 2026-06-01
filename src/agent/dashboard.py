"""Build dashboard context payloads for the right-hand canvas."""

from __future__ import annotations

import json
from typing import Any


def _parse_obs(observation: str) -> dict[str, Any] | None:
    try:
        return json.loads(observation)
    except json.JSONDecodeError:
        return None


def _trace_lookup(trace: list[dict[str, Any]]) -> dict[str, Any]:
    site_info = None
    visit_date = None
    weather_data = None
    price_data = None

    for row in trace:
        tool = row.get("tool")
        obs = _parse_obs(row.get("observation") or "")
        if not obs:
            continue
        if tool == "resolve_site":
            site_info = obs
        elif tool == "parse_visit_date":
            visit_date = obs.get("usingDate")
        elif tool == "get_weather_forecast":
            weather_data = obs
        elif tool == "get_ticket_prices":
            price_data = obs

    return {
        "site_info": site_info,
        "visit_date": visit_date,
        "weather": weather_data,
        "price": price_data,
    }


def build_dashboard_from_trace(trace: list[dict[str, Any]]) -> dict[str, Any] | None:
    ctx = _trace_lookup(trace)
    site = ctx.get("site_info") or {}
    weather = ctx.get("weather")
    price = ctx.get("price")

    if not site and not weather and not price:
        return None

    using_date = (
        (price or {}).get("usingDate")
        or (weather or {}).get("usingDate")
        or ctx.get("visit_date")
        or ""
    )

    destination = {
        "region": site.get("region", ""),
        "siteName": site.get("siteName") or (price or {}).get("siteName", ""),
        "supplierCode": site.get("supplierCode")
        or (price or {}).get("supplierCode", ""),
        "usingDate": using_date,
    }

    focus = "destination"
    if weather and not price:
        focus = "weather"
    elif price:
        focus = "prices"
    elif weather:
        focus = "weather"

    dash: dict[str, Any] = {
        "focus": focus,
        "destination": destination,
    }

    if weather and "error" not in weather:
        dash["weather"] = {
            "location": weather.get("location"),
            "usingDate": weather.get("usingDate"),
            "tempC": weather.get("tempC"),
            "feelsLikeC": weather.get("feelsLikeC"),
            "description": weather.get("description"),
            "icon": weather.get("icon"),
            "humidity": weather.get("humidity"),
            "windMs": weather.get("windMs"),
            "popPercent": weather.get("popPercent"),
            "hasRain": weather.get("hasRain"),
            "rainRisk": weather.get("rainRisk"),
            "recommendation": weather.get("recommendation"),
            "suggestReschedule": weather.get("suggestReschedule"),
            "nextDayDate": weather.get("nextDayDate"),
            "nextDayHasRain": weather.get("nextDayHasRain"),
        }

    if price and price.get("tickets"):
        from src.agent.structured import build_chat_structured

        structured = build_chat_structured(trace)
        if structured and structured.get("priceQuote"):
            dash["priceQuote"] = structured["priceQuote"]

    return dash


def build_dashboard_after_tool(
    tool: str, observation: str, trace: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Incremental dashboard update when a tool completes."""
    _ = tool, observation
    return build_dashboard_from_trace(trace)
