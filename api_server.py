"""
FastAPI server — exposes chatbot/agent for the React UI.

Run:
  py api_server.py
  # or: py -m uvicorn api_server:app --reload --port 8000
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.agent.agent import ReActAgent
from src.chatbot.chatbot import Chatbot
from src.core.provider_factory import create_provider, reload_env
from src.telemetry.logger import logger
from src.tools import get_tool_definitions

load_dotenv(override=True)

app = FastAPI(title="C2 Team 040 AI Chat Bot API", version="1.0.0")

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


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    mode: str = Field(default="agent", pattern="^(agent|chatbot)$")
    provider: str | None = None


class ChatResponse(BaseModel):
    reply: str
    reasoning_steps: list[str] = []
    mode: str
    provider: str = ""


@app.get("/api/health")
def health():
    reload_env()
    return {
        "status": "ok",
        "provider": os.getenv("DEFAULT_PROVIDER", "deepseek"),
        "model": os.getenv("DEFAULT_MODEL", "deepseek-v4-flash"),
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    reload_env()
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    provider_name = req.provider or os.getenv("DEFAULT_PROVIDER", "deepseek")

    try:
        llm = create_provider(req.provider)
        logger.log_event(
            "API_CHAT",
            {"provider": provider_name, "model": llm.model_name, "mode": req.mode},
        )

        if req.mode == "chatbot":
            bot = Chatbot(llm)
            reply = bot.run(message)
            return ChatResponse(
                reply=reply,
                reasoning_steps=[],
                mode="chatbot",
                provider=provider_name,
            )

        agent = ReActAgent(llm, get_tool_definitions(), max_steps=6, prompt_version="v2")
        reply = agent.run(message)
        return ChatResponse(
            reply=reply,
            reasoning_steps=agent.get_reasoning_steps(),
            mode="agent",
            provider=provider_name,
        )

    except Exception as e:
        logger.log_event(
            "API_ERROR",
            {"error": str(e), "message": message[:200], "provider": provider_name},
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    reload_env()
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=True)
