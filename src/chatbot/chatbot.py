from typing import Optional

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class Chatbot:
    """Minimal chatbot baseline — single LLM call, no tools."""

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def get_system_prompt(self) -> str:
        return (
            "You are a helpful e-commerce shopping assistant. "
            "Answer customer questions about products, discounts, and shipping. "
            "If you don't know exact prices or stock, say so honestly."
        )

    def run(self, user_input: str) -> str:
        logger.log_event("CHATBOT_START", {"input": user_input, "model": self.llm.model_name})

        result = self.llm.generate(user_input, system_prompt=self.get_system_prompt())
        content = result["content"]

        tracker.track_request(
            provider=result.get("provider", "unknown"),
            model=self.llm.model_name,
            usage=result["usage"],
            latency_ms=result["latency_ms"],
        )

        logger.log_event("CHATBOT_END", {"response_length": len(content)})
        return content
