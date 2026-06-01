"""CLI to test the VinWonders ReAct agent."""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

from src.agent.agent import ReActAgent
from src.core.factory import get_llm_provider
from src.tools.registry import VINWONDERS_TOOLS


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="VinWonders ReAct agent CLI")
    parser.add_argument("question", nargs="?", help="User question")
    parser.add_argument(
        "--version",
        choices=["v1", "v2"],
        default="v2",
        help="v1=minimal ReAct, v2=bootstrap+guardrails",
    )
    args = parser.parse_args()

    question = args.question or input("Bạn: ").strip()
    if not question:
        return

    agent = ReActAgent(
        get_llm_provider(),
        VINWONDERS_TOOLS,
        max_steps=10,
        prompt_version=args.version,
    )
    print("\n[Agent đang xử lý — có thể mất 30–90s nếu tra giá vé...]\n")
    answer = agent.run(question)
    print("Agent:", answer)
    if agent.trace:
        print("\n--- Trace ---")
        for row in agent.trace:
            print(row)


if __name__ == "__main__":
    main()
