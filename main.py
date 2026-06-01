"""
Lab 3 Runner — Chatbot baseline vs ReAct Agent.

Usage:
  python main.py chatbot "What is AI?"
  python main.py agent "Buy 2 iPhones with WINNER, ship to Hanoi. Total price?"
  python main.py compare
  python main.py test --provider openai
  python main.py test --provider google
"""

import argparse
import os
import sys

from dotenv import load_dotenv

from src.agent.agent import ReActAgent
from src.chatbot.chatbot import Chatbot
from src.core.provider_factory import create_provider
from src.telemetry.logger import logger
from src.tools import get_tool_definitions

TEST_CASES = [
    {
        "name": "Simple Q&A",
        "query": "What products do you sell?",
        "expect_agent_tools": False,
    },
    {
        "name": "Multi-step purchase",
        "query": "I want to buy 2 iPhones using code WINNER and ship to Hanoi. What is the total price?",
        "expect_agent_tools": True,
    },
    {
        "name": "Stock check",
        "query": "Is MacBook Air in stock and what is the price?",
        "expect_agent_tools": True,
    },
]


def run_chatbot(query: str, provider: str | None = None) -> str:
    llm = create_provider(provider)
    bot = Chatbot(llm)
    return bot.run(query)


def run_agent(query: str, provider: str | None = None, version: str = "v2") -> str:
    llm = create_provider(provider)
    tools = get_tool_definitions()
    agent = ReActAgent(llm, tools, max_steps=6, prompt_version=version)
    return agent.run(query)


def run_compare(provider: str | None = None):
    query = TEST_CASES[1]["query"]
    print("=" * 60)
    print("QUERY:", query)
    print("=" * 60)

    print("\n--- CHATBOT (baseline) ---")
    chatbot_answer = run_chatbot(query, provider)
    print(chatbot_answer)

    print("\n--- AGENT v2 (ReAct) ---")
    agent_answer = run_agent(query, provider, version="v2")
    print(agent_answer)


def run_test_suite(provider: str | None = None):
    print(f"\nRunning test suite (provider={provider or os.getenv('DEFAULT_PROVIDER')})...\n")
    results = []

    for case in TEST_CASES:
        print(f"\n{'=' * 60}\nTest: {case['name']}\nQuery: {case['query']}\n{'=' * 60}")
        try:
            chatbot_out = run_chatbot(case["query"], provider)
            agent_out = run_agent(case["query"], provider, version="v2")
            print(f"\n[Chatbot]\n{chatbot_out[:300]}...")
            print(f"\n[Agent]\n{agent_out[:300]}...")
            results.append({"case": case["name"], "status": "OK"})
        except Exception as e:
            logger.log_event("TEST_ERROR", {"case": case["name"], "error": str(e)})
            print(f"ERROR: {e}")
            results.append({"case": case["name"], "status": "FAIL", "error": str(e)})

    print(f"\n{'=' * 60}\nSUMMARY\n{'=' * 60}")
    for r in results:
        print(f"  {r['case']}: {r['status']}")
    print(f"\nLogs saved to logs/ — check LLM_METRIC events for latency & tokens.")


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Lab 3: Chatbot vs ReAct Agent")
    sub = parser.add_subparsers(dest="command", required=True)

    p_chat = sub.add_parser("chatbot", help="Run chatbot baseline")
    p_chat.add_argument("query", nargs="?", default="Hello!")
    p_chat.add_argument("--provider", choices=["deepseek", "openai", "google", "local"])

    p_agent = sub.add_parser("agent", help="Run ReAct agent")
    p_agent.add_argument("query", nargs="?", default="Check iPhone stock.")
    p_agent.add_argument("--provider", choices=["deepseek", "openai", "google", "local"])
    p_agent.add_argument("--version", choices=["v1", "v2"], default="v2")

    p_cmp = sub.add_parser("compare", help="Compare chatbot vs agent on multi-step query")
    p_cmp.add_argument("--provider", choices=["deepseek", "openai", "google", "local"])

    p_test = sub.add_parser("test", help="Run full test suite")
    p_test.add_argument("--provider", choices=["deepseek", "openai", "google", "local"])

    args = parser.parse_args()

    try:
        if args.command == "chatbot":
            print(run_chatbot(args.query, args.provider))
        elif args.command == "agent":
            print(run_agent(args.query, args.provider, args.version))
        elif args.command == "compare":
            run_compare(args.provider)
        elif args.command == "test":
            run_test_suite(args.provider)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
