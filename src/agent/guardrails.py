"""Agent guardrails — premature Final Answer rejection (Agent v2)."""

from __future__ import annotations

from typing import Any


def tools_used(trace: list[dict[str, Any]]) -> set[str]:
    return {row.get("tool") for row in trace if row.get("tool")}


def pipeline_complete(trace: list[dict[str, Any]]) -> bool:
    used = tools_used(trace)
    return "get_weather_forecast" in used and "get_ticket_prices" in used


def reject_premature_final(
    trace: list[dict[str, Any]],
    *,
    requires_pipeline: bool,
) -> str | None:
    """
  Return observation text to inject when model tries Final Answer too early.
  Used only in Agent v2 when `requires_pipeline` is True.
    """
    if not requires_pipeline:
        return None
    if pipeline_complete(trace):
        return None

    used = tools_used(trace)
    missing: list[str] = []
    for name in (
        "resolve_site",
        "parse_visit_date",
        "get_weather_forecast",
        "get_ticket_prices",
    ):
        if name not in used:
            missing.append(name)

    if not missing:
        return None

    return (
        "CHƯA ĐƯỢC PHÉP Final Answer. Còn thiếu tool: "
        + ", ".join(missing)
        + ". Gọi đúng thứ tự resolve_site → parse_visit_date → "
        "get_weather_forecast → get_ticket_prices. Không bịa giá/thời tiết."
    )
