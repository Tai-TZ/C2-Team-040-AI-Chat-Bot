"""Build structured UI payloads from agent tool trace."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlencode

from src.agent.destination_maps import build_destination_map_payload
from src.agent.trace import trace_context
from src.utils.money import format_vnd

_GUESTS_RE = re.compile(r"(\d+)\s*người", re.IGNORECASE)


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


def ensure_followup_question(answer: str) -> str:
    """Karphany always ends with an open question."""
    text = (answer or "").strip()
    if not text:
        return (
            "Mình sẵn sàng tư vấn VinWonders cho bạn. "
            "Bạn muốn đi khu nào và ngày nào?"
        )
    if text.endswith("?") or text.endswith("？"):
        return text
    return (
        f"{text}\n\n"
        "Bạn muốn mình **đặt loại vé nào**, **đổi ngày**, hay **gợi ý combo tiết kiệm** hơn?"
    )


def _merge_actions(
    primary: list[dict[str, Any]], extra: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for item in [*primary, *extra]:
        aid = str(item.get("id", ""))
        if not aid or aid in seen:
            continue
        seen.add(aid)
        merged.append(item)
    return merged[:8]


def build_interaction_actions(
    *,
    site_name: str = "",
    region: str = "",
    supplier_code: str = "",
    using_date: str = "",
    has_prices: bool = False,
) -> list[dict[str, Any]]:
    """Quick-reply buttons shown under every assistant message."""
    label_site = site_name or region or "VinWonders"
    actions: list[dict[str, Any]] = []

    if supplier_code and using_date:
        actions.append(
            {
                "id": "book",
                "label": "Đặt trên VinWonders",
                "kind": "link",
                "href": _booking_url(supplier_code, using_date),
            }
        )
        actions.append(
            {
                "id": "tab-prices",
                "label": "Mở bảng giá chi tiết",
                "kind": "tab",
                "tab": "tickets",
                "supplierCode": supplier_code,
                "usingDate": using_date,
            }
        )

    if using_date and label_site:
        actions.extend(
            [
                {
                    "id": "combo-save",
                    "label": "Gợi ý combo tiết kiệm",
                    "kind": "message",
                    "text": (
                        f"Gợi ý combo vé tiết kiệm nhất tại {label_site} "
                        f"ngày {using_date}"
                    ),
                },
                {
                    "id": "change-date",
                    "label": "Đổi ngày khác",
                    "kind": "message",
                    "text": (
                        f"Xem thời tiết và giá vé {label_site} vào ngày khác giúp mình"
                    ),
                },
                {
                    "id": "itinerary",
                    "label": "Lên lịch trình",
                    "kind": "message",
                    "text": (
                        f"Lên lịch trình 2 ngày 1 đêm tại {label_site} "
                        f"vào ngày {using_date}"
                    ),
                },
            ]
        )

    if not has_prices and label_site and using_date:
        actions.insert(
            0,
            {
                "id": "refresh-prices",
                "label": "Tra lại giá vé",
                "kind": "message",
                "text": (
                    f"Tra lại giá vé {label_site} ngày {using_date} "
                    "và gợi ý loại phù hợp"
                ),
            },
        )

    if not actions:
        actions = [
            {
                "id": "explore-nt",
                "label": "Nha Trang cuối tuần sau",
                "kind": "message",
                "text": (
                    "Mình muốn đi Nha Trang cuối tuần sau, "
                    "check thời tiết và giá vé"
                ),
            },
            {
                "id": "explore-hn",
                "label": "Hà Nội ngày mai",
                "kind": "message",
                "text": "Xem thời tiết và giá VinWonders Hà Nội ngày mai",
            },
            {
                "id": "explore-pq",
                "label": "Phú Quốc tuần sau",
                "kind": "message",
                "text": "Cho mình xem Phú Quốc tuần sau — thời tiết và giá vé",
            },
        ]

    actions.append(
        {
            "id": "other-dest",
            "label": "Điểm đến khác",
            "kind": "message",
            "text": "Liệt kê các điểm VinWonders và gợi ý ngày đẹp để đi",
        }
    )
    return actions


def _weather_actions(
    weather_data: dict[str, Any],
    *,
    region: str,
    site_name: str,
    using_date: str,
) -> list[dict[str, Any]]:
    if not weather_data.get("suggestReschedule"):
        return []
    next_day = weather_data.get("nextDayDate", "")
    label = site_name or region
    return [
        {
            "id": "reschedule",
            "label": f"Dời sang {next_day or 'ngày mai'}",
            "kind": "message",
            "text": f"Cho tôi xem thời tiết và giá vé {label} vào ngày {next_day}",
        },
        {
            "id": "keep-date",
            "label": "Vẫn đi ngày này",
            "kind": "message",
            "text": (
                f"Vẫn giữ ngày {using_date}, xem giá vé và gợi ý trong nhà tại {label}"
            ),
        },
    ]


def _weather_card(weather_data: dict[str, Any]) -> dict[str, Any]:
    return {
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


def build_chat_structured(trace: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Extract ticket cards, weather, map, and suggested actions from agent trace."""
    ctx = trace_context(trace)
    site_info = ctx.get("site_info") or {}
    weather_data = ctx.get("weather")
    price_data = ctx.get("price")

    has_prices = bool(price_data and price_data.get("tickets"))
    has_weather = bool(weather_data and "error" not in weather_data)
    destination_map = (
        build_destination_map_payload(ctx.get("region", ""))
        if ctx.get("region")
        else None
    )
    if not has_prices and not has_weather and not destination_map:
        return None

    supplier_code = (price_data or {}).get("supplierCode") or site_info.get(
        "supplierCode", ""
    )
    using_date = (
        (price_data or {}).get("usingDate")
        or (weather_data or {}).get("usingDate")
        or ctx.get("using_date")
        or ctx.get("visit_date")
        or ""
    )
    site_name = (price_data or {}).get("siteName") or site_info.get("siteName", "")
    region = site_info.get("region") or ctx.get("region", "")

    actions = _weather_actions(
        weather_data or {},
        region=region,
        site_name=site_name,
        using_date=using_date,
    )
    actions = _merge_actions(
        actions,
        build_interaction_actions(
            site_name=site_name,
            region=region,
            supplier_code=supplier_code,
            using_date=using_date,
            has_prices=has_prices,
        ),
    )

    result: dict[str, Any] = {"actions": actions}
    if destination_map:
        result["destinationMap"] = destination_map
    if has_weather:
        result["weather"] = _weather_card(weather_data)

    if not has_prices:
        return result

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
                "salePriceFormatted": format_vnd(int(sale)),
                "originalPrice": t.get("originalPrice"),
                "originalPriceFormatted": (
                    format_vnd(int(t["originalPrice"]))
                    if t.get("originalPrice")
                    else None
                ),
                "isCheapest": i == 0,
            }
        )

    cheapest = tickets[0] if tickets else None
    result["priceQuote"] = {
        "siteName": site_name,
        "region": region,
        "supplierCode": supplier_code,
        "usingDate": using_date,
        "bookingUrl": _booking_url(supplier_code, using_date),
        "cheapestTicketName": cheapest["name"] if cheapest else price_data.get(
            "cheapestTicketName"
        ),
        "cheapestFormatted": (
            cheapest["salePriceFormatted"]
            if cheapest
            else price_data.get("cheapestFormatted")
        ),
        "tickets": tickets,
    }
    return result


def finalize_structured_payload(trace: list[dict[str, Any]]) -> dict[str, Any]:
    """Structured data + interaction buttons for the chat UI."""
    return build_chat_structured(trace) or {
        "actions": build_interaction_actions(),
    }


def build_fallback_answer(
    trace: list[dict[str, Any]], *, user_input: str = ""
) -> str | None:
    """Vietnamese summary from tool trace when the LLM call fails."""
    structured = build_chat_structured(trace)
    if not structured:
        return None

    parts: list[str] = []
    weather = structured.get("weather")
    quote = structured.get("priceQuote")

    if weather:
        loc = weather.get("location") or "điểm đến"
        day = weather.get("usingDate") or ""
        desc = weather.get("description") or ""
        temp = weather.get("tempC")
        temp_s = f"{temp}°C" if temp is not None else ""
        rain = weather.get("popPercent")
        rain_s = f", khả năng mưa ~{rain}%" if rain is not None else ""
        parts.append(
            f"**Thời tiết {loc}** ({day}): {desc} {temp_s}{rain_s}.".strip()
        )
        rec = weather.get("recommendation")
        if rec:
            parts.append(rec)

    if quote:
        site = quote.get("siteName") or quote.get("region") or "VinWonders"
        day = quote.get("usingDate") or ""
        cheapest = quote.get("cheapestFormatted") or "—"
        ticket_name = quote.get("cheapestTicketName") or "vé"
        parts.append(
            f"**{site}** ({day}): loại rẻ nhất hiện tại là *{ticket_name}* từ **{cheapest}**/vé."
        )
        guests = _GUESTS_RE.search(user_input)
        if guests:
            n = max(1, int(guests.group(1)))
            tickets = quote.get("tickets") or []
            if tickets and tickets[0].get("salePrice"):
                total = int(tickets[0]["salePrice"]) * n
                parts.append(
                    f"Ước tính cho **{n} người** (cùng loại vé rẻ nhất): khoảng **{format_vnd(total)}**."
                )

    if not parts:
        return None

    parts.append(
        "Bạn xem thêm thẻ giá và bảng bên phải; chọn nút bên dưới để đặt vé hoặc đổi ngày."
    )
    return ensure_followup_question("\n\n".join(parts))
