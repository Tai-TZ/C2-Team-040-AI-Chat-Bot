"""Offline tests aligned with SCORING.md (no API keys)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent.agent import ReActAgent
from src.agent.guardrails import reject_premature_final
from src.agent.structured import build_chat_structured
from src.chatbot.vinwonders_chatbot import build_chatbot_system_prompt
from src.prompts.vinwonders import build_agent_system_prompt_v1
from src.tools.registry import VINWONDERS_TOOLS, execute_tool
from src.vinwonders.destinations_data import find_region_name_in_text


def test_chatbot_baseline_prompt():
    p = build_chatbot_system_prompt()
    assert "VinWonders" in p
    assert "không" in p.lower()


def test_agent_v1_v2_prompts_differ():
    tools = "\n- resolve_site: test"
    v1 = build_agent_system_prompt_v1(tools)
    assert "Karphany" not in v1
    from src.prompts.vinwonders import build_agent_system_prompt

    v2 = build_agent_system_prompt(tools)
    assert "Karphany" in v2


def test_guardrail_blocks_early_final():
    trace = [{"tool": "resolve_site", "observation": "{}"}]
    msg = reject_premature_final(trace, requires_pipeline=True)
    assert msg and "get_weather_forecast" in msg


def test_structured_map_from_resolve_trace():
    obs = execute_tool("resolve_site", {"query": "Nha Trang"})
    structured = build_chat_structured(
        [{"tool": "resolve_site", "observation": obs}]
    )
    assert structured is not None
    assert structured.get("destinationMap") is not None


def test_bootstrap_finds_nha_trang():
    assert find_region_name_in_text("Đi Nha Trang cuối tuần") == "Nha Trang"


def test_react_agent_vinwonders_tools_mock():
    class MockLLM:
        model_name = "mock"
        step = 0
        responses = [
            'Thought: Tìm site.\nAction: resolve_site(query="Nha Trang")',
            'Thought: Ngày.\nAction: parse_visit_date(expression="cuối tuần sau")',
            "Thought: Done.\nFinal Answer: Đã tra cứu Nha Trang.",
        ]

        def generate(self, prompt, system_prompt=None):
            content = self.responses[min(self.step, len(self.responses) - 1)]
            self.step += 1
            return {
                "content": content,
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                "latency_ms": 50,
                "provider": "mock",
            }

    agent = ReActAgent(
        MockLLM(), VINWONDERS_TOOLS, max_steps=6, prompt_version="v1"
    )
    answer = agent.run("Nha Trang cuối tuần sau")
    assert "Nha Trang" in answer or "tra" in answer.lower()
    assert any(t.get("tool") == "resolve_site" for t in agent.trace)


def test_trace_export_shape():
    obs = execute_tool("resolve_site", {"query": "Phú Quốc"})
    row = {
        "step": 1,
        "thought": "test",
        "tool": "resolve_site",
        "args": {"query": "Phú Quốc"},
        "observation": json.loads(obs),
    }
    assert row["observation"].get("region") == "Phú Quốc"
