"""Auto-run VinWonders tool pipeline when the model passes bad tool args."""

from __future__ import annotations

import re
from typing import Any, Callable, Generator

from src.agent.trace import trace_context
from src.vinwonders.destinations_data import find_region_name_in_text

_DATE_PHRASES = (
    "cuối tuần sau",
    "cuối tuần này",
    "cuối tuần",
    "ngày mai",
    "ngày kia",
    "tuần sau",
    "hôm nay",
)


def extract_date_expression(user_input: str) -> str | None:
    lower = user_input.lower()
    for phrase in _DATE_PHRASES:
        if phrase in lower:
            return phrase
    m = re.search(r"\d{1,2}[/.-]\d{1,2}[/.-]\d{4}", user_input)
    return m.group(0) if m else None


def run_bootstrap_pipeline(
    user_input: str,
    trace: list[dict[str, Any]],
    *,
    execute_tool: Callable[[str, dict[str, Any]], str],
    tools_used: Callable[[], set[str]],
    on_tool_done: Callable[[str, str, str, dict[str, Any]], Generator[dict[str, Any], None, None]],
) -> Generator[dict[str, Any], None, None]:
    """
    Pre-run resolve_site → parse_visit_date → weather → prices
    so the model cannot waste steps on invalid arguments.
    """
    used = tools_used()
    loc = find_region_name_in_text(user_input)
    date_expr = extract_date_expression(user_input) or "cuối tuần sau"

    if loc and "resolve_site" not in used:
        observation = execute_tool("resolve_site", {"query": loc})
        yield from on_tool_done("resolve_site", "resolve_site", observation, {"query": loc})
        used = tools_used()

    if date_expr and "parse_visit_date" not in used:
        observation = execute_tool("parse_visit_date", {"expression": date_expr})
        yield from on_tool_done(
            "parse_visit_date", "parse_visit_date", observation, {"expression": date_expr}
        )
        used = tools_used()

    ctx = trace_context(trace)
    region = ctx.get("region") or ""
    using_date = ctx.get("using_date") or ""
    supplier_code = ctx.get("supplier_code") or ""

    if region and using_date and "get_weather_forecast" not in used:
        args = {"location": region, "using_date": using_date}
        observation = execute_tool("get_weather_forecast", args)
        yield from on_tool_done("get_weather_forecast", "get_weather_forecast", observation, args)
        used = tools_used()

    if supplier_code and using_date and "get_ticket_prices" not in used:
        args = {"supplier_code": supplier_code, "using_date": using_date}
        observation = execute_tool("get_ticket_prices", args)
        yield from on_tool_done("get_ticket_prices", "get_ticket_prices", observation, args)
