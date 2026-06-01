"""Tool registry for the VinWonders ReAct agent."""

from __future__ import annotations

import json
from typing import Any, Callable

from src.tools.dates import parse_visit_date
from src.tools.destinations import list_destinations, resolve_site
from src.tools.prices import get_ticket_prices_tool

VINWONDERS_TOOLS: list[dict[str, Any]] = [
    {
        "name": "list_destinations",
        "description": (
            "Liệt kê khu vực và mã địa điểm (supplierCode). "
            'Tham số tùy chọn region_query, ví dụ region_query="Nha Trang".'
        ),
        "parameters": {"region_query": "optional string"},
    },
    {
        "name": "resolve_site",
        "description": (
            "Tìm supplierCode từ tên địa điểm tiếng Việt/Anh (vd: Nha Trang, Phú Quốc). "
            'Tham số bắt buộc: query="tên địa điểm".'
        ),
        "parameters": {"query": "string"},
    },
    {
        "name": "parse_visit_date",
        "description": (
            "Chuyển ngày tự nhiên hoặc DD-MM-YYYY sang định dạng DD-MM-YYYY. "
            'Ví dụ expression="cuối tuần sau" hoặc "20-06-2026".'
        ),
        "parameters": {"expression": "string"},
    },
    {
        "name": "get_ticket_prices",
        "description": (
            "Lấy giá vé VinWonders thật theo mã địa điểm và ngày. "
            "Bắt buộc trước khi báo giá cho khách. "
            'Tham số: supplier_code="NTVW1", using_date="20-06-2026".'
        ),
        "parameters": {"supplier_code": "string", "using_date": "string"},
    },
]

_HANDLERS: dict[str, Callable[..., str]] = {
    "list_destinations": list_destinations,
    "resolve_site": resolve_site,
    "parse_visit_date": parse_visit_date,
    "get_ticket_prices": get_ticket_prices_tool,
}


def execute_tool(tool_name: str, args: dict[str, Any]) -> str:
    handler = _HANDLERS.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"}, ensure_ascii=False)
    try:
        return handler(**args)
    except TypeError as exc:
        return json.dumps(
            {"error": f"Invalid arguments for {tool_name}: {exc}"},
            ensure_ascii=False,
        )
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)
