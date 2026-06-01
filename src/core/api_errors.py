"""Map exceptions to HTTP status codes and structured API error payloads."""

from __future__ import annotations

from typing import Dict, Tuple

try:
    from openai import (
        APIConnectionError,
        APIStatusError,
        APITimeoutError,
        AuthenticationError,
        BadRequestError,
        NotFoundError,
        PermissionDeniedError,
        RateLimitError,
    )
except ImportError:  # pragma: no cover
    APIConnectionError = None  # type: ignore
    APIStatusError = None  # type: ignore
    APITimeoutError = None  # type: ignore
    AuthenticationError = None  # type: ignore
    BadRequestError = None  # type: ignore
    NotFoundError = None  # type: ignore
    PermissionDeniedError = None  # type: ignore
    RateLimitError = None  # type: ignore


def error_detail(code: str, message: str) -> Dict[str, str]:
    return {"code": code, "message": message}


def exception_to_http(exc: Exception) -> Tuple[int, Dict[str, str]]:
    """
    Returns (http_status, detail_dict) for FastAPI HTTPException.
    detail_dict: {"code": str, "message": str}
    """
    msg = str(exc).strip() or exc.__class__.__name__
    lower = msg.lower()

    # --- OpenAI / DeepSeek (OpenAI-compatible SDK) ---
    if RateLimitError and isinstance(exc, RateLimitError):
        return 429, error_detail("rate_limit", _friendly_rate_limit(msg))

    if AuthenticationError and isinstance(exc, AuthenticationError):
        return 401, error_detail(
            "auth_error",
            "API key không hợp lệ hoặc đã hết hạn. Kiểm tra DEEPSEEK_API_KEY / OPENAI_API_KEY trong .env.",
        )

    if PermissionDeniedError and isinstance(exc, PermissionDeniedError):
        return 403, error_detail("permission_denied", msg)

    if BadRequestError and isinstance(exc, BadRequestError):
        return 400, error_detail("bad_request", msg)

    if NotFoundError and isinstance(exc, NotFoundError):
        return 404, error_detail("model_not_found", f"Model không tồn tại hoặc không khả dụng: {msg}")

    if APITimeoutError and isinstance(exc, APITimeoutError):
        return 504, error_detail("timeout", "LLM API phản hồi quá chậm. Thử lại sau.")

    if APIConnectionError and isinstance(exc, APIConnectionError):
        return 502, error_detail(
            "upstream_unreachable",
            "Không kết nối được tới LLM API. Kiểm tra mạng và DEEPSEEK_BASE_URL.",
        )

    if APIStatusError and isinstance(exc, APIStatusError):
        status = getattr(exc, "status_code", None) or 502
        if status == 429:
            return 429, error_detail("rate_limit", _friendly_rate_limit(msg))
        if status in (401, 403):
            return status, error_detail("auth_error", msg)
        if 400 <= status < 500:
            return status, error_detail("upstream_client_error", msg)
        return 502, error_detail("upstream_error", msg)

    # --- Config / local ---
    if isinstance(exc, ValueError):
        if "api_key" in lower or "chưa được cấu hình" in lower:
            return 503, error_detail("config_error", msg)
        if "unknown provider" in lower:
            return 400, error_detail("invalid_provider", msg)
        return 400, error_detail("validation_error", msg)

    if isinstance(exc, FileNotFoundError):
        return 503, error_detail(
            "model_missing",
            f"Không tìm thấy file model local: {msg}",
        )

    # --- Heuristics from message text (Gemini, generic) ---
    if "429" in msg or "quota" in lower or "rate limit" in lower or "resource_exhausted" in lower:
        return 429, error_detail("rate_limit", _friendly_rate_limit(msg))

    if "401" in msg or "unauthorized" in lower or "invalid api key" in lower or "authentication" in lower:
        return 401, error_detail("auth_error", "Xác thực API thất bại. Kiểm tra API key trong .env.")

    if "timeout" in lower or "timed out" in lower:
        return 504, error_detail("timeout", "Yêu cầu quá thời gian chờ. Thử lại.")

    if "connection" in lower or "connect" in lower:
        return 502, error_detail("upstream_unreachable", "Không kết nối được dịch vụ AI.")

    return 500, error_detail("internal_error", msg)


def _friendly_rate_limit(raw: str) -> str:
    return (
        "API đã vượt giới hạn (rate limit / quota). "
        "Đợi vài phút hoặc đổi provider trong .env (DEFAULT_PROVIDER=deepseek)."
    )
