import os
from typing import Optional

from src.core.gemini_provider import GeminiProvider
from src.core.llm_provider import LLMProvider
from src.core.openai_provider import OpenAIProvider


def create_provider(
    provider_name: Optional[str] = None,
    model_name: Optional[str] = None,
) -> LLMProvider:
    provider = (provider_name or os.getenv("DEFAULT_PROVIDER", "openai")).lower()
    model = model_name or os.getenv("DEFAULT_MODEL", "gpt-4o")

    if provider == "openai":
        return OpenAIProvider(model_name=model, api_key=os.getenv("OPENAI_API_KEY"))
    if provider in ("google", "gemini"):
        gemini_model = model if model.startswith("gemini") else "gemini-2.0-flash"
        return GeminiProvider(model_name=gemini_model, api_key=os.getenv("GEMINI_API_KEY"))
    if provider == "local":
        from src.core.local_provider import LocalProvider

        path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        return LocalProvider(model_path=path)

    raise ValueError(f"Unknown provider: {provider}. Use openai | google | local")
