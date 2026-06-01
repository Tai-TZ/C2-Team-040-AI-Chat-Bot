"""FastAPI: VinWonders prices + ReAct agent chat."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.agent.agent import ReActAgent
from src.core.factory import get_llm_provider
from src.llm import ds2api
from src.tools.registry import VINWONDERS_TOOLS
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


@lru_cache(maxsize=1)
def _get_agent() -> ReActAgent:
    return ReActAgent(get_llm_provider(), VINWONDERS_TOOLS, max_steps=8)


def _conversation_context(messages: list[ChatMessage]) -> str | None:
    """Prior turns (excluding latest user message)."""
    if len(messages) <= 1:
        return None
    lines: list[str] = []
    for m in messages[:-1]:
        role = "Khách" if m.role == "user" else "AI"
        lines.append(f"{role}: {m.content}")
    return "\n".join(lines[-10:])


def _latest_user_message(messages: list[ChatMessage]) -> str:
    for m in reversed(messages):
        if m.role == "user":
            return m.content
    raise HTTPException(400, "No user message in request")


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
        agent = _get_agent()
        text = agent.run(
            _latest_user_message(req.messages),
            conversation_context=_conversation_context(req.messages),
        )
        from src.agent.structured import build_chat_structured

        structured = build_chat_structured(agent.trace)
        return {
            "content": text,
            "model": agent.llm.model_name,
            "agent": True,
            "trace": agent.trace,
            "structured": structured,
        }
    except ValueError as exc:
        raise HTTPException(500, str(exc)) from exc
    except ConnectionError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Agent error: {exc}") from exc


def _sse_payload(obj: dict[str, Any]) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    try:
        agent = _get_agent()
        user_msg = _latest_user_message(req.messages)
        context = _conversation_context(req.messages)

        def generate():
            try:
                for event in agent.run_with_events(
                    user_msg, conversation_context=context
                ):
                    if event.get("type") == "trace":
                        yield _sse_payload(
                            {
                                "type": "trace",
                                "message": event.get("message", ""),
                            }
                        )
                    elif event.get("type") == "structured":
                        yield _sse_payload(
                            {
                                "type": "structured",
                                "data": event.get("data"),
                            }
                        )
                    elif event.get("type") == "dashboard":
                        yield _sse_payload(
                            {
                                "type": "dashboard",
                                "data": event.get("data"),
                            }
                        )
                    elif event.get("type") == "content":
                        yield _sse_payload(
                            {
                                "choices": [
                                    {
                                        "delta": {
                                            "content": event.get("delta", "")
                                        }
                                    }
                                ]
                            }
                        )
                yield "data: [DONE]\n\n"
            except Exception as exc:
                yield _sse_payload({"type": "error", "message": str(exc)})
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream; charset=utf-8",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except ValueError as exc:
        raise HTTPException(500, str(exc)) from exc
    except ConnectionError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Agent error: {exc}") from exc


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
