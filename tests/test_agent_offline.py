"""Offline tests — no API keys required."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent import ReActAgent
from src.tools.ecommerce_tools import check_stock, get_discount, calc_shipping, calc_total, get_tool_definitions


def test_tools():
    assert "999" in check_stock("iphone")
    assert "15%" in get_discount("WINNER")
    assert "Shipping" in calc_shipping(0.4, "hanoi")
    assert "TOTAL" in calc_total(1998, 15, 5.8)
    print("[OK] Tools")


def test_agent_tool_execution():
    """Test ReAct tool parsing & execution without calling LLM."""

    class MockLLM:
        model_name = "mock"
        step = 0
        responses = [
            "Thought: Check stock.\nAction: check_stock(iphone)",
            "Thought: Done.\nFinal Answer: iPhone costs $999, 50 in stock.",
        ]

        def generate(self, prompt, system_prompt=None):
            content = self.responses[min(self.step, len(self.responses) - 1)]
            self.step += 1
            return {
                "content": content,
                "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                "latency_ms": 100,
                "provider": "mock",
            }

    agent = ReActAgent(MockLLM(), get_tool_definitions(), max_steps=5)
    result = agent.run("Check iPhone stock")
    assert "999" in result or "stock" in result.lower()
    print(f"[OK] Agent loop -> {result[:80]}...")


if __name__ == "__main__":
    test_tools()
    test_agent_tool_execution()
    print("\nAll offline tests passed.")
