"""Baseline chatbot (no tools) — compare with ReAct agent for Lab 3."""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

from src.chatbot.vinwonders_chatbot import VinWondersChatbot
from src.core.factory import get_llm_provider


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="VinWonders baseline chatbot")
    parser.add_argument("question", nargs="?", help="User question")
    args = parser.parse_args()

    question = args.question or input("Bạn: ").strip()
    if not question:
        return

    print("\nChatbot:", VinWondersChatbot(get_llm_provider()).run(question))


if __name__ == "__main__":
    main()
