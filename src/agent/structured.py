"""Build structured UI payloads from agent tool trace."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode


def _booking_url(supplier_code: str, using_date: str) -> str:
    params = urlencode(
        {
            "code": supplier_code,
            "usingDate": using_date,
            "style": "b",
            "tab": "all",
        }
    )
    return f"https://booking.vinwonders.com/vi-VND/search?{params}"


def _format_vnd(amount: int) -> str:
    return f"{amount:,} đ".replace(",", ".")


def build_chat_structured(trace: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Extract ticket cards, weather, and suggested actions from agent trace."""
    price_data: dict[str, Any] | None = None
    site_info: dict[str, Any] | None = None
    weather_data: dict[str, Any] | None = None
    visit_date_expr: str | None = None

    for row in trace:
        tool = row.get("tool")
        if tool == "resolve_site":
            try:
                site_info = json.loads(row.get("observation") or "{}")
            except json.JSONDecodeError:
                pass
        if tool == "parse_visit_date":
            try:
                parsed = json.loads(row.get("observation") or "{}")
                visit_date_expr = parsed.get("usingDate")
            except json.JSONDecodeError:
                pass
        if tool == "get_weather_forecast":
            try:
                weather_data = json.loads(row.get("observation") or "{}")
            except json.JSONDecodeError:
                pass
        if tool == "get_ticket_prices":
            try:
                price_data = json.loads(row.get("observation") or "{}")
            except json.JSONDecodeError:
                pass

    has_prices = bool(price_data and price_data.get("tickets"))
    has_weather = bool(weather_data and "error" not in weather_data)
    if not has_prices and not has_weather:
        return None

    supplier_code = (price_data or {}).get("supplierCode") or (site_info or {}).get(
        "supplierCode", ""
    )
    using_date = (
        (price_data or {}).get("usingDate")
        or (weather_data or {}).get("usingDate")
        or visit_date_expr
        or ""
    )
    site_name = (
        (price_data or {}).get("siteName")
        or (site_info or {}).get("siteName")
        or ""
    )
    region = (site_info or {}).get("region", "")

    tickets_raw = (price_data or {}).get("tickets") or []
    tickets_sorted = sorted(
        tickets_raw,
        key=lambda t: (t.get("salePrice") is None, t.get("salePrice") or 10**12),
    )
    tickets = []
    for i, t in enumerate(tickets_sorted[:6]):
        sale = t.get("salePrice")
        if sale is None:
            continue
        tickets.append(
            {
                "name": t.get("name", "Vé"),
                "salePrice": sale,
                "salePriceFormatted": _format_vnd(int(sale)),
                "originalPrice": t.get("originalPrice"),
                "originalPriceFormatted": (
                    _format_vnd(int(t["originalPrice"]))
                    if t.get("originalPrice")
                    else None
                ),
                "isCheapest": i == 0,
            }
        )

    cheapest = tickets[0] if tickets else None
    region_label = region or site_name or "điểm đến"

    actions: list[dict[str, Any]] = []

    if has_weather and weather_data.get("suggestReschedule"):
        next_day = weather_data.get("nextDayDate", "")
        actions.append(
            {
                "id": "reschedule",
                "label": f"Dời sang {next_day or 'ngày mai'}",
                "kind": "message",
                "text": f"Cho tôi xem thời tiết và giá vé {region or site_name} vào ngày {next_day}",
            }
        )
        actions.append(
            {
                "id": "keep-date",
                "label": "Vẫn đi ngày này",
                "kind": "message",
                "text": f"Vẫn giữ ngày {using_date}, xem giá vé và gợi ý trong nhà tại {site_name or region}",
            }
        )

    if has_prices and supplier_code:
        actions.extend(
            [
        {
            "id": "book",
            "label": "Đặt trên VinWonders",
            "kind": "link",
            "href": _booking_url(supplier_code, using_date),
        },
        {
            "id": "tab-prices",
            "label": "Mở tab Vé & Chuyến bay",
            "kind": "tab",
            "tab": "tickets",
            "supplierCode": supplier_code,
            "usingDate": using_date,
        },
        {
            "id": "itinerary",
            "label": "Lên lịch trình",
            "kind": "message",
            "text": f"Lên lịch trình 2 ngày 1 đêm tại {region_label} vào ngày {using_date}",
        },
        {
            "id": "change-date",
            "label": "Đổi ngày khác",
            "kind": "message",
            "text": f"Xem giá vé {site_name or region_label} vào ngày khác giúp tôi",
        },
        {
            "id": "more-combo",
            "label": "Gợi ý combo tiết kiệm",
            "kind": "message",
            "text": f"Gợi ý combo vé tiết kiệm nhất tại {site_name or region_label} ngày {using_date}",
        },
            ]
        )

    result: dict[str, Any] = {"actions": actions}

    if has_weather:
        result["weather"] = {
            "location": weather_data.get("location"),
            "usingDate": weather_data.get("usingDate"),
            "tempC": weather_data.get("tempC"),
            "feelsLikeC": weather_data.get("feelsLikeC"),
            "description": weather_data.get("description"),
            "icon": weather_data.get("icon"),
            "humidity": weather_data.get("humidity"),
            "windMs": weather_data.get("windMs"),
            "popPercent": weather_data.get("popPercent"),
            "hasRain": weather_data.get("hasRain"),
            "rainRisk": weather_data.get("rainRisk"),
            "recommendation": weather_data.get("recommendation"),
            "suggestReschedule": weather_data.get("suggestReschedule"),
        }

    if not has_prices:
        return result

    result["priceQuote"] = {
            "siteName": site_name,
            "region": region,
            "supplierCode": supplier_code,
            "usingDate": using_date,
            "bookingUrl": _booking_url(supplier_code, using_date),
            "cheapestTicketName": cheapest["name"] if cheapest else price_data.get(
                "cheapestTicketName"
            ),
            "cheapestFormatted": cheapest["salePriceFormatted"]
            if cheapest
            else price_data.get("cheapestFormatted"),
            "tickets": tickets,
        }
    return result
