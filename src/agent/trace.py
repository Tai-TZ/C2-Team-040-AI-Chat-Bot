"""Parse agent tool trace rows into structured context."""

from __future__ import annotations

import json
from typing import Any


def parse_observation(observation: str) -> dict[str, Any]:
    try:
        return json.loads(observation or "{}")
    except json.JSONDecodeError:
        return {}


def trace_context(trace: list[dict[str, Any]]) -> dict[str, Any]:
    """Latest tool observations merged into one context dict."""
    ctx: dict[str, Any] = {
        "site_info": None,
        "visit_date": None,
        "weather": None,
        "price": None,
        "region": "",
        "site_name": "",
        "supplier_code": "",
        "using_date": "",
    }

    for row in trace:
        tool = row.get("tool")
        data = parse_observation(row.get("observation") or "")
        if data.get("error"):
            continue

        if tool == "resolve_site":
            ctx["site_info"] = data
            ctx["region"] = data.get("region") or ctx["region"]
            ctx["site_name"] = data.get("siteName") or ctx["site_name"]
            ctx["supplier_code"] = data.get("supplierCode") or ctx["supplier_code"]
        elif tool == "parse_visit_date":
            ctx["visit_date"] = data.get("usingDate")
            ctx["using_date"] = data.get("usingDate") or ctx["using_date"]
        elif tool == "get_weather_forecast":
            ctx["weather"] = data
            ctx["using_date"] = data.get("usingDate") or ctx["using_date"]
            ctx["region"] = data.get("location") or ctx["region"]
        elif tool == "get_ticket_prices":
            ctx["price"] = data
            ctx["supplier_code"] = data.get("supplierCode") or ctx["supplier_code"]
            ctx["using_date"] = data.get("usingDate") or ctx["using_date"]
            ctx["site_name"] = data.get("siteName") or ctx["site_name"]

    return ctx
