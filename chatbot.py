"""Baseline chatbot (no tools) — compare with ReAct agent for Lab 3."""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

from src.core.factory import get_llm_provider
from src.prompts.vinwonders import build_destinations_summary


def build_chatbot_prompt() -> str:
    destinations = build_destinations_summary()
    return f"""Bạn là VinWonders Tour Guide AI, trả lời tiếng Việt.
Các điểm đến:
{destinations}

Quy tắc: ngắn gọn; nếu hỏi giá cụ thể, nhắc khách dùng tab Vé & Chuyến bay (KHÔNG có tool tra giá).
"""


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="VinWonders baseline chatbot")
    parser.add_argument("question", nargs="?", help="User question")
    args = parser.parse_args()

    question = args.question or input("Bạn: ").strip()
    if not question:
        return

    llm = get_llm_provider()
    result = llm.generate(question, system_prompt=build_chatbot_prompt())
    print("\nChatbot:", result.get("content", ""))


if __name__ == "__main__":
    main()
