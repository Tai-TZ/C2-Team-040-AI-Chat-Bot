"""DS2API client (OpenAI-compatible chat completions)."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Generator

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError

DEFAULT_BASE_URL = "https://deep-seek-api-kappa.vercel.app"
DEFAULT_MODEL = "deepseek-v4-flash"
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3


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
            last_exc: Exception | None = None
            for attempt in range(_MAX_RETRIES):
                resp = requests.post(
                    url, headers=_headers(), json=payload, timeout=timeout
                )
                if resp.status_code in _RETRYABLE_STATUS and attempt < _MAX_RETRIES - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                try:
                    resp.raise_for_status()
                except HTTPError as exc:
                    last_exc = exc
                    if (
                        resp.status_code in _RETRYABLE_STATUS
                        and attempt < _MAX_RETRIES - 1
                    ):
                        time.sleep(1.5 * (attempt + 1))
                        continue
                    raise _friendly_http_error(exc, resp) from exc
                return json.loads(resp.content.decode("utf-8"))
            if last_exc:
                raise last_exc
            raise RuntimeError("DS2API request failed without response")

        resp = requests.post(
            url, headers=_headers(), json=payload, stream=True, timeout=timeout
        )
        resp.raise_for_status()
        resp.encoding = "utf-8"
    except RequestsConnectionError as exc:
        raise ConnectionError(_connection_hint(exc)) from exc
    except HTTPError as exc:
        raise _friendly_http_error(exc, exc.response) from exc

    def _iter_lines() -> Generator[str, None, None]:
        # Decode bytes as UTF-8 — requests defaults SSE to ISO-8859-1 (breaks Vietnamese).
        for line in resp.iter_lines():
            if line:
                yield line.decode("utf-8")

    return _iter_lines()


def _friendly_http_error(exc: HTTPError, resp: requests.Response | None) -> RuntimeError:
    status = resp.status_code if resp is not None else 0
    body_preview = ""
    if resp is not None:
        try:
            body_preview = resp.text[:200]
        except Exception:
            body_preview = ""
    if status in _RETRYABLE_STATUS:
        return RuntimeError(
            f"DS2API tạm lỗi (HTTP {status}). Đã thử lại {_MAX_RETRIES} lần. "
            "Thử lại sau vài giây hoặc kiểm tra DS2API_API_KEY / DS2API_BASE_URL."
            + (f" Chi tiết: {body_preview}" if body_preview else "")
        )
    if status in (401, 403):
        return RuntimeError(
            f"DS2API từ chối API key (HTTP {status}). Kiểm tra DS2API_API_KEY trong .env."
        )
    return RuntimeError(str(exc))


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
