"""VinWonders chatbot baseline — single LLM call, no tools (Lab 3 § Chatbot Baseline)."""

from __future__ import annotations

from src.core.llm_provider import LLMProvider
from src.prompts.vinwonders import build_destinations_summary
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


def build_chatbot_system_prompt() -> str:
    destinations = build_destinations_summary()
    return f"""Bạn là **VinWonders Tour Guide** (chatbot baseline — không có tool).

## Điểm đến (tĩnh, có thể lỗi thời)
{destinations}

## Quy tắc
- Trả lời tiếng Việt, ngắn gọn, thân thiện.
- **Không** có quyền tra giá vé hay thời tiết thật — nếu khách hỏi giá/ngày cụ thể, nói rõ bạn chỉ gợi ý chung và mời dùng agent có tool hoặc tab Vé.
- Không bịa số tiền VND cụ thể.
"""


class VinWondersChatbot:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def run(self, user_input: str) -> str:
        logger.log_event(
            "CHATBOT_START",
            {"input": user_input, "model": self.llm.model_name, "variant": "vinwonders"},
        )
        result = self.llm.generate(
            user_input, system_prompt=build_chatbot_system_prompt()
        )
        content = result.get("content", "")

        tracker.track_request(
            provider=result.get("provider", "unknown"),
            model=self.llm.model_name,
            usage=result.get("usage", {}),
            latency_ms=result.get("latency_ms", 0),
        )
        logger.log_event("CHATBOT_END", {"response_length": len(content)})
        return content
