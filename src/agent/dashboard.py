"""Build dashboard context payloads for the right-hand canvas."""

from __future__ import annotations

from typing import Any

from src.agent.structured import build_chat_structured
from src.agent.trace import trace_context


def build_dashboard_from_trace(trace: list[dict[str, Any]]) -> dict[str, Any] | None:
    ctx = trace_context(trace)
    site = ctx.get("site_info") or {}
    weather = ctx.get("weather")
    price = ctx.get("price")

    if not site and not weather and not price:
        return None

    using_date = (
        (price or {}).get("usingDate")
        or (weather or {}).get("usingDate")
        or ctx.get("using_date")
        or ctx.get("visit_date")
        or ""
    )

    destination = {
        "region": site.get("region", "") or ctx.get("region", ""),
        "siteName": site.get("siteName") or (price or {}).get("siteName", ""),
        "supplierCode": site.get("supplierCode")
        or (price or {}).get("supplierCode", ""),
        "usingDate": using_date,
    }

    if price:
        focus = "prices"
    elif weather:
        focus = "weather"
    else:
        focus = "destination"

    dash: dict[str, Any] = {"focus": focus, "destination": destination}

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

    structured = build_chat_structured(trace)
    if structured and structured.get("priceQuote"):
        dash["priceQuote"] = structured["priceQuote"]

    return dash


def build_dashboard_after_tool(
    _tool: str, _observation: str, trace: list[dict[str, Any]]
) -> dict[str, Any] | None:
    return build_dashboard_from_trace(trace)
