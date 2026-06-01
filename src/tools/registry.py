"""Tool registry for the VinWonders ReAct agent."""

from __future__ import annotations

import json
from typing import Any, Callable

from src.tools.dates import parse_visit_date
from src.tools.destinations import list_destinations, resolve_site
from src.tools.prices import get_ticket_prices_tool
from src.tools.weather import get_weather_forecast

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
        "name": "get_weather_forecast",
        "description": (
            "Kiểm tra thời tiết dự báo tại địa điểm vào ngày đi (BẮT BUỘC trước khi tư vấn vé). "
            'Tham số: location="Nha Trang", using_date="21-06-2026". '
            "Nếu hasRain=true, hỏi khách có muốn dời ngày hoặc gợi ý hoạt động trong nhà."
        ),
        "parameters": {"location": "string", "using_date": "string"},
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
    "get_weather_forecast": get_weather_forecast,
    "get_ticket_prices": get_ticket_prices_tool,
}


def _is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    s = str(value).strip()
    if not s:
        return True
    if s.startswith("[") and "bước" in s.lower():
        return True
    return False


def _sanitize_tool_args(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Keep only valid params; map common model mistakes to the right keys."""
    raw = {k: v for k, v in (args or {}).items() if not _is_placeholder(v)}

    if tool_name == "resolve_site":
        q = raw.get("query") or raw.get("location") or raw.get("region") or raw.get("siteName")
        return {"query": str(q).strip()} if q else {}

    if tool_name == "parse_visit_date":
        e = raw.get("expression") or raw.get("date_text") or raw.get("date")
        return {"expression": str(e).strip()} if e else {}

    if tool_name == "get_weather_forecast":
        location = raw.get("location") or raw.get("region") or raw.get("siteName")
        using_date = raw.get("using_date") or raw.get("usingDate")
        out: dict[str, Any] = {}
        if location:
            out["location"] = str(location).strip()
        if using_date:
            out["using_date"] = str(using_date).strip()
        return out

    if tool_name == "get_ticket_prices":
        code = raw.get("supplier_code") or raw.get("supplierCode")
        using_date = raw.get("using_date") or raw.get("usingDate")
        out = {}
        if code:
            out["supplier_code"] = str(code).strip().upper()
        if using_date:
            out["using_date"] = str(using_date).strip()
        return out

    if tool_name == "list_destinations":
        q = raw.get("region_query") or raw.get("region") or raw.get("query")
        return {"region_query": str(q).strip()} if q else {}

    return raw


def execute_tool(tool_name: str, args: dict[str, Any]) -> str:
    handler = _HANDLERS.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"}, ensure_ascii=False)
    clean = _sanitize_tool_args(tool_name, args)
    if tool_name in ("resolve_site", "parse_visit_date", "get_weather_forecast", "get_ticket_prices"):
        required = {
            "resolve_site": ("query",),
            "parse_visit_date": ("expression",),
            "get_weather_forecast": ("location", "using_date"),
            "get_ticket_prices": ("supplier_code", "using_date"),
        }[tool_name]
        missing = [k for k in required if k not in clean or not str(clean[k]).strip()]
        if missing:
            return json.dumps(
                {
                    "error": f"Thiếu tham số: {', '.join(missing)}. "
                    f"Chỉ truyền đúng tham số cho {tool_name}, không thêm field khác.",
                },
                ensure_ascii=False,
            )
    try:
        return handler(**clean)
    except TypeError as exc:
        return json.dumps(
            {"error": f"Invalid arguments for {tool_name}: {exc}"},
            ensure_ascii=False,
        )
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)
