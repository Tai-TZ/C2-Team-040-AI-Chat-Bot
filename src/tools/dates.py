"""Parse Vietnamese relative dates to DD-MM-YYYY."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta


def _normalize_expr(expression: str) -> str:
    import unicodedata

    text = expression.lower().strip()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def _next_saturday(from_date: datetime, *, weeks_ahead: int = 0) -> datetime:
    days_until_sat = (5 - from_date.weekday()) % 7
    if days_until_sat == 0:
        days_until_sat = 7
    return from_date + timedelta(days=days_until_sat + weeks_ahead * 7)


def _parse_fixed_date(expression: str) -> datetime | None:
    m = re.search(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", expression)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return datetime(y, mo, d)
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", expression)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return datetime(y, mo, d)
    return None


def parse_visit_date(expression: str) -> str:
    """Convert natural language or DD-MM-YYYY to VinWonders date (DD-MM-YYYY)."""
    today = datetime.now()
    fixed = _parse_fixed_date(expression)
    if fixed:
        result = fixed
        note = "exact date"
    else:
        e = _normalize_expr(expression)
        if "ngay mai" in e or "mai" == e:
            result = today + timedelta(days=1)
            note = "tomorrow"
        elif "ngay kia" in e:
            result = today + timedelta(days=2)
            note = "day after tomorrow"
        elif "cuoi tuan sau" in e or "cuoi tuan toi" in e:
            result = _next_saturday(today, weeks_ahead=1)
            note = "next weekend (Saturday)"
        elif "cuoi tuan nay" in e or "tuan nay" in e:
            result = _next_saturday(today, weeks_ahead=0)
            note = "this weekend (Saturday)"
        elif "tuan sau" in e:
            result = today + timedelta(days=7)
            note = "about one week ahead"
        elif "hom nay" in e:
            result = today
            note = "today"
        else:
            result = today + timedelta(days=7)
            note = "default +7 days (could not parse expression)"

    return json.dumps(
        {
            "expression": expression,
            "usingDate": result.strftime("%d-%m-%Y"),
            "isoDate": result.strftime("%Y-%m-%d"),
            "weekday": result.strftime("%A"),
            "note": note,
        },
        ensure_ascii=False,
    )
