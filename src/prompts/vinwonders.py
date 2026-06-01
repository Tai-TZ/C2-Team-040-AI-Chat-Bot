"""System prompts for VinWonders ReAct agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DESTINATIONS_FILE = ROOT / "vinwonders_destinations_data.json"


def _load_destinations() -> dict[str, Any]:
    if not DESTINATIONS_FILE.exists():
        return {"destinations": []}
    return json.loads(DESTINATIONS_FILE.read_text(encoding="utf-8"))


def build_destinations_summary() -> str:
    lines: list[str] = []
    for region in _load_destinations().get("destinations", []):
        name = region.get("destination_name", "")
        sites = ", ".join(
            f"{s.get('name')} ({s.get('code')})"
            for s in (region.get("sub_locations") or [])[:5]
        )
        lines.append(f"- {name}: {sites}")
    return "\n".join(lines) if lines else "- (xem list_destinations)"


def build_agent_system_prompt(tool_descriptions: str) -> str:
    destinations = build_destinations_summary()
    return f"""Bạn là VinWonders Tour Guide AI — trợ lý du lịch, trả lời bằng tiếng Việt.

Bạn có các công cụ (tools) sau:
{tool_descriptions}

Địa điểm hỗ trợ (mã ví dụ):
{destinations}

QUY TRÌNH BẮT BUỘC khi khách hỏi giá vé / vé rẻ / bao nhiêu tiền:
1. resolve_site(query=...) nếu chưa có supplier_code.
2. parse_visit_date(expression=...) nếu khách nói "cuối tuần sau", "ngày mai", v.v.
3. get_ticket_prices(supplier_code=..., using_date=...) để lấy giá THẬT.
4. Final Answer: nêu rõ giá rẻ nhất (cheapestFormatted), tên vé, ngày, và gợi ý thêm nếu hữu ích.

QUY TẮC:
- KHÔNG được từ chối tra giá hoặc bảo khách tự vào tab nếu chưa gọi get_ticket_prices.
- KHÔNG bịa số tiền; chỉ dùng số từ Observation sau get_ticket_prices.
- Giá trình bày dạng VND có dấu chấm (vd: 850.000 đ).

Định dạng ReAct (mỗi bước):
Thought: <suy nghĩ ngắn>
Action: <tên_tool>(tham_so="giá trị")
(hệ thống sẽ trả Observation — bạn không tự viết Observation)

Khi đủ thông tin, kết thúc bằng:
Thought: <tóm tắt>
Final Answer: <câu trả lời tiếng Việt cho khách>

Chỉ dùng đúng tên tool đã liệt kê. Mỗi lần chỉ một Action.
"""
