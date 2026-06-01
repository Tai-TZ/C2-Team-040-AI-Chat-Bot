"""
Lab 3 runner — VinWonders Chatbot baseline vs ReAct Agent v1/v2.

Usage:
  python main.py chatbot "Nha Trang cuối tuần sau giá bao nhiêu?"
  python main.py agent "Nha Trang cuối tuần sau" --version v2
  python main.py compare
  python main.py eval --offline
  python scripts/eval_lab3.py --offline
"""

from __future__ import annotations

import argparse
import json
import sys

from dotenv import load_dotenv

from src.agent.agent import ReActAgent
from src.chatbot.vinwonders_chatbot import VinWondersChatbot
from src.core.factory import get_llm_provider
from src.telemetry.metrics import tracker
from src.tools.registry import VINWONDERS_TOOLS

VINWONDERS_EVAL_CASES = [
    {
        "id": "multi_step_price",
        "name": "Multi-step: weather + price",
        "query": "Mình muốn đi Nha Trang cuối tuần sau, check thời tiết và giá vé",
        "expect_tools": True,
    },
    {
        "id": "attractions",
        "name": "Attractions + map",
        "query": "Nha Trang có gì chơi?",
        "expect_tools": True,
    },
    {
        "id": "off_topic",
        "name": "Off-topic refusal",
        "query": "Viết code Python sort list",
        "expect_tools": False,
    },
]


def run_chatbot(query: str) -> str:
    llm = get_llm_provider()
    return VinWondersChatbot(llm).run(query)


def run_agent(query: str, version: str = "v2") -> str:
    llm = get_llm_provider()
    agent = ReActAgent(llm, VINWONDERS_TOOLS, max_steps=10, prompt_version=version)
    return agent.run(query)


def run_compare() -> None:
    case = VINWONDERS_EVAL_CASES[0]
    query = case["query"]
    print("=" * 60)
    print("QUERY:", query)
    print("=" * 60)

    print("\n--- CHATBOT (baseline, no tools) ---")
    print(run_chatbot(query)[:800])

    print("\n--- AGENT v1 (ReAct, no bootstrap/guards) ---")
    print(run_agent(query, version="v1")[:800])

    print("\n--- AGENT v2 (bootstrap + guardrails + Karphany) ---")
    print(run_agent(query, version="v2")[:800])

    print("\n--- TELEMETRY ---")
    print(json.dumps(tracker.session_summary(), indent=2, ensure_ascii=False))


def run_eval_offline() -> None:
    from scripts.eval_lab3 import run_offline_suite

    run_offline_suite()


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Lab 3: VinWonders Chatbot vs Agent")
    sub = parser.add_subparsers(dest="command", required=True)

    p_chat = sub.add_parser("chatbot", help="VinWonders chatbot baseline")
    p_chat.add_argument("query", nargs="?", default="Xin chào VinWonders!")

    p_agent = sub.add_parser("agent", help="VinWonders ReAct agent")
    p_agent.add_argument("query", nargs="?", default="Nha Trang cuối tuần sau")
    p_agent.add_argument("--version", choices=["v1", "v2"], default="v2")

    sub.add_parser("compare", help="Compare chatbot vs agent v1 vs v2")

    p_eval = sub.add_parser("eval", help="Run evaluation suite")
    p_eval.add_argument("--offline", action="store_true", help="No API keys required")

    args = parser.parse_args()

    try:
        if args.command == "chatbot":
            print(run_chatbot(args.query))
        elif args.command == "agent":
            print(run_agent(args.query, args.version))
        elif args.command == "compare":
            run_compare()
        elif args.command == "eval":
            if args.offline:
                run_eval_offline()
            else:
                print("Use: python scripts/eval_lab3.py --live for API evaluation")
                run_eval_offline()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
