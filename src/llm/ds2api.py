"""DS2API client (OpenAI-compatible chat completions)."""

from __future__ import annotations

import json
import os
from typing import Any, Generator, Iterable

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError

DEFAULT_BASE_URL = "https://deep-seek-api-kappa.vercel.app"
DEFAULT_MODEL = "deepseek-v4-flash"


def _base_url() -> str:
    return os.getenv("DS2API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _api_key() -> str:
    key = os.getenv("DS2API_API_KEY", "").strip()
    if not key:
        raise ValueError("DS2API_API_KEY is not set in environment")
    return key


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }


def _connection_hint(exc: Exception) -> str:
    base = _base_url()
    return (
        f"Không kết nối được DS2API tại {base}. "
        "Hãy chạy DS2API trước (mặc định port 5001), ví dụ: "
        "`go run .` hoặc binary DS2API trong thư mục dự án DS2API. "
        "Nếu deploy remote, sửa DS2API_BASE_URL trong file .env. "
        f"Chi tiết: {exc}"
    )


def chat_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    stream: bool = False,
    timeout: int = 120,
) -> dict[str, Any] | Generator[str, None, None]:
    """Call DS2API POST /v1/chat/completions."""
    payload = {
        "model": model or os.getenv("DS2API_MODEL", DEFAULT_MODEL),
        "messages": messages,
        "stream": stream,
    }
    url = f"{_base_url()}/v1/chat/completions"

    try:
        if not stream:
            resp = requests.post(
                url, headers=_headers(), json=payload, timeout=timeout
            )
            resp.raise_for_status()
            return resp.json()

        resp = requests.post(
            url, headers=_headers(), json=payload, stream=True, timeout=timeout
        )
        resp.raise_for_status()
    except RequestsConnectionError as exc:
        raise ConnectionError(_connection_hint(exc)) from exc

    def _iter_lines() -> Generator[str, None, None]:
        for line in resp.iter_lines(decode_unicode=True):
            if line is not None:
                yield line

    return _iter_lines()


def check_health() -> dict[str, Any]:
    """Probe DS2API liveness."""
    url = f"{_base_url()}/healthz"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except RequestsConnectionError as exc:
        raise ConnectionError(_connection_hint(exc)) from exc


def extract_assistant_text(completion: dict[str, Any]) -> str:
    choices = completion.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return (message.get("content") or "").strip()


def parse_sse_content_line(line: str) -> str | None:
    """Parse one SSE line; return text delta if present."""
    if not line.startswith("data:"):
        return None
    data = line[5:].strip()
    if not data or data == "[DONE]":
        return None
    try:
        chunk = json.loads(data)
    except json.JSONDecodeError:
        return None
    choices = chunk.get("choices") or []
    if not choices:
        return None
    delta = choices[0].get("delta") or {}
    content = delta.get("content")
    return content if isinstance(content, str) and content else None
