"""Factory for LLM providers used by the agent."""

from __future__ import annotations

import os

from src.core.ds2api_provider import DS2APIProvider
from src.core.llm_provider import LLMProvider


def get_llm_provider() -> LLMProvider:
    # Agent web app: AGENT_PROVIDER=openrouter | ds2api | openai | ...
    provider = os.getenv("AGENT_PROVIDER", "openrouter")
    provider = provider.lower().strip()

    if provider in ("openrouter", "or"):
        from src.core.openai_provider import OpenAIProvider

        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY chưa được cấu hình trong .env")
        model = (
            os.getenv("AGENT_MODEL")
            or os.getenv("OPENROUTER_MODEL")
            or "deepseek/deepseek-chat"
        )
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        return OpenAIProvider(
            model_name=model,
            api_key=api_key,
            base_url=base_url,
            provider_label="openrouter",
            extra_headers={
                "HTTP-Referer": os.getenv(
                    "OPENROUTER_HTTP_REFERER", "http://localhost:8080"
                ),
                "X-Title": os.getenv(
                    "OPENROUTER_APP_TITLE", "VinWonders Tour Guide"
                ),
            },
        )

    if provider in ("ds2api", "deepseek"):
        model = (
            os.getenv("AGENT_MODEL")
            or os.getenv("DS2API_MODEL")
            or "deepseek-v4-flash"
        )
        return DS2APIProvider(model_name=model)

    model = os.getenv("AGENT_MODEL") or os.getenv("DEFAULT_MODEL")

    if provider in ("openai", "gpt"):
        from src.core.openai_provider import OpenAIProvider

        return OpenAIProvider(
            model_name=model or "gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    if provider in ("google", "gemini"):
        from src.core.gemini_provider import GeminiProvider

        return GeminiProvider(
            model_name=model or "gemini-1.5-flash",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

    if provider == "local":
        from src.core.local_provider import LocalProvider

        return LocalProvider(
            model_name=model or "local",
            api_key=os.getenv("LOCAL_MODEL_PATH"),
        )

    return DS2APIProvider(model_name=model)
