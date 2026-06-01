"""Ticket price tool wrapping the VinWonders crawler."""

from __future__ import annotations

import json
import re

from src.utils.money import format_vnd
from src.vinwonders.crawler import get_ticket_prices


def _normalize_date(date: str) -> str:
    date = date.strip()
    if re.match(r"^\d{2}-\d{2}-\d{4}$", date):
        return date
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        y, m, d = date.split("-")
        return f"{d}-{m}-{y}"
    raise ValueError("using_date must be DD-MM-YYYY or YYYY-MM-DD")


def get_ticket_prices_tool(supplier_code: str, using_date: str) -> str:
    """Fetch live ticket prices; includes cheapest ticket summary."""
    code = supplier_code.strip().upper()
    visit_date = _normalize_date(using_date)

    try:
        data = get_ticket_prices(code, visit_date, detailed=False)
    except Exception as exc:
        return json.dumps(
            {"error": str(exc), "supplierCode": code, "usingDate": visit_date},
            ensure_ascii=False,
        )

    tickets = data.get("tickets") or []
    priced = [t for t in tickets if t.get("salePrice") is not None]
    cheapest_row = min(priced, key=lambda t: t["salePrice"]) if priced else None
    cheapest = cheapest_row["salePrice"] if cheapest_row else None

    payload = {
        "supplierCode": data.get("supplierCode"),
        "usingDate": data.get("usingDate"),
        "siteName": data.get("siteName"),
        "ticketCount": data.get("ticketCount", 0),
        "tickets": priced[:15],
        "cheapestVnd": cheapest,
        "cheapestFormatted": format_vnd(cheapest) if cheapest is not None else None,
        "cheapestTicketName": cheapest_row.get("name") if cheapest_row else None,
    }
    return json.dumps(payload, ensure_ascii=False)
