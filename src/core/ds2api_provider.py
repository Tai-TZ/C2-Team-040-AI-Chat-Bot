"""LLMProvider implementation using DS2API (OpenAI-compatible)."""

from __future__ import annotations

import os
import time
from typing import Any, Generator, Optional

from src.core.llm_provider import LLMProvider
from src.llm import ds2api


class DS2APIProvider(LLMProvider):
    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
    ):
        model = model_name or os.getenv("DS2API_MODEL", "deepseek-v4-flash")
        super().__init__(model, api_key or os.getenv("DS2API_API_KEY"))
        self.provider_name = "ds2api"

    def generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> dict[str, Any]:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        start = time.time()
        result = ds2api.chat_completion(
            messages, stream=False, model=self.model_name
        )
        assert isinstance(result, dict)
        latency_ms = int((time.time() - start) * 1000)

        usage_raw = result.get("usage") or {}
        usage = {
            "prompt_tokens": usage_raw.get("prompt_tokens", 0),
            "completion_tokens": usage_raw.get("completion_tokens", 0),
            "total_tokens": usage_raw.get("total_tokens", 0),
        }

        return {
            "content": ds2api.extract_assistant_text(result),
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": self.provider_name,
        }

    def stream(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> Generator[str, None, None]:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        lines = ds2api.chat_completion(messages, stream=True, model=self.model_name)
        assert not isinstance(lines, dict)
        for line in lines:
            delta = ds2api.parse_sse_content_line(line)
            if delta:
                yield delta
