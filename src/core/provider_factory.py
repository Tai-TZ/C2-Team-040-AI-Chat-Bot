import os
from typing import Optional

from dotenv import load_dotenv

from src.core.llm_provider import LLMProvider
from src.core.openai_provider import OpenAIProvider


def reload_env() -> None:
    """Reload .env on each request — uvicorn --reload does not refresh env vars."""
    load_dotenv(override=True)


def _deepseek_base_url() -> str:
    base = os.getenv("DEEPSEEK_BASE_URL", "https://deep-seek-api-kappa.vercel.app/v1")
    base = base.rstrip("/")
    if not base.endswith("/v1"):
        base = f"{base}/v1"
    return base


def create_provider(
    provider_name: Optional[str] = None,
    model_name: Optional[str] = None,
) -> LLMProvider:
    reload_env()

    provider = (provider_name or os.getenv("DEFAULT_PROVIDER", "deepseek")).lower()
    model = model_name or os.getenv("DEFAULT_MODEL", "deepseek-v4-flash")

    if provider in ("deepseek", "ds2api"):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY chưa được cấu hình trong .env")
        return OpenAIProvider(
            model_name=model,
            api_key=api_key,
            base_url=_deepseek_base_url(),
            provider_label="deepseek",
        )

    if provider == "openai":
        return OpenAIProvider(model_name=model, api_key=os.getenv("OPENAI_API_KEY"))

    if provider in ("google", "gemini"):
        from src.core.gemini_provider import GeminiProvider

        gemini_model = model if model.startswith("gemini") else "gemini-2.0-flash"
        return GeminiProvider(model_name=gemini_model, api_key=os.getenv("GEMINI_API_KEY"))

    if provider == "local":
        from src.core.local_provider import LocalProvider

        path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        return LocalProvider(model_path=path)

    raise ValueError(
        f"Unknown provider: {provider}. Use deepseek | openai | google | local"
    )
