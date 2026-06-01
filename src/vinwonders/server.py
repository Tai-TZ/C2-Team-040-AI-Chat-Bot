"""FastAPI: VinWonders prices + DS2API chat proxy."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.llm import ds2api
from src.vinwonders.crawler import get_ticket_prices

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=True)
DESTINATIONS_FILE = ROOT / "vinwonders_destinations_data.json"

app = FastAPI(title="VinWonders API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_destinations() -> dict:
    if not DESTINATIONS_FILE.exists():
        raise HTTPException(500, "vinwonders_destinations_data.json not found")
    return json.loads(DESTINATIONS_FILE.read_text(encoding="utf-8"))


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    stream: bool = False


def _build_system_prompt() -> str:
    dest_lines: list[str] = []
    try:
        data = _load_destinations()
        for region in data.get("destinations", []):
            name = region.get("destination_name", "")
            sites = ", ".join(
                s.get("name", "") for s in region.get("sub_locations", [])[:6]
            )
            dest_lines.append(f"- {name}: {sites}")
    except Exception:
        pass

    destinations_block = (
        "\n".join(dest_lines) if dest_lines else "- Xem tab Vé & Chuyến bay trên giao diện."
    )

    return f"""Bạn là VinWonders Tour Guide AI — trợ lý du lịch thân thiện, trả lời bằng tiếng Việt.

Nhiệm vụ: tư vấn lịch trình, gợi ý vé VinWonders, combo, show và mẹo tiết kiệm.
Người dùng có thể tra cứu **giá vé thật** ở tab "Vé & Chuyến bay" (chọn khu vực, địa điểm, ngày).

Các điểm đến hỗ trợ:
{destinations_block}

Quy tắc:
- Ngắn gọn, có bullet khi liệt kê; không bịa giá — nếu cần giá cụ thể hãy nhắc dùng tab tra cứu vé.
- Ưu tiên gợi ý thực tế (thời gian, di chuyển, combo vé+show).
"""


def _chat_messages(user_messages: list[ChatMessage]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": _build_system_prompt()},
        *[{"role": m.role, "content": m.content} for m in user_messages],
    ]


def _normalize_date(date: str) -> str:
    """Accept DD-MM-YYYY or YYYY-MM-DD → DD-MM-YYYY."""
    if re.match(r"^\d{2}-\d{2}-\d{4}$", date):
        return date
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        y, m, d = date.split("-")
        return f"{d}-{m}-{y}"
    raise HTTPException(400, "date must be DD-MM-YYYY or YYYY-MM-DD")


@app.get("/api/health")
def health():
    llm_ok = False
    llm_error = None
    try:
        ds2api.check_health()
        llm_ok = True
    except Exception as exc:
        llm_error = str(exc)

    return {
        "status": "ok",
        "ds2api": {"ok": llm_ok, "error": llm_error},
    }


@app.post("/api/chat")
def chat(req: ChatRequest):
    if req.stream:
        raise HTTPException(400, "Use POST /api/chat/stream for streaming")

    try:
        result = ds2api.chat_completion(
            _chat_messages(req.messages), stream=False
        )
        assert isinstance(result, dict)
        text = ds2api.extract_assistant_text(result)
        return {"content": text, "model": result.get("model")}
    except ValueError as exc:
        raise HTTPException(500, str(exc)) from exc
    except ConnectionError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"DS2API error: {exc}") from exc


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    try:
        stream = ds2api.chat_completion(
            _chat_messages(req.messages), stream=True
        )
        assert not isinstance(stream, dict)

        def generate():
            for line in stream:
                yield f"{line}\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except ValueError as exc:
        raise HTTPException(500, str(exc)) from exc
    except ConnectionError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"DS2API error: {exc}") from exc


@app.get("/api/destinations")
def destinations():
    return _load_destinations()


@app.get("/api/prices")
def prices(
    code: str = Query(..., min_length=2, description="Supplier code, e.g. NTVW1"),
    date: str = Query(..., description="Visit date DD-MM-YYYY or YYYY-MM-DD"),
    detailed: bool = Query(False),
):
    using_date = _normalize_date(date)
    try:
        return get_ticket_prices(code, using_date, detailed=detailed)
    except Exception as exc:
        raise HTTPException(502, f"Failed to fetch prices: {exc}") from exc


def main():
    import uvicorn

    uvicorn.run(
        "src.vinwonders.server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
