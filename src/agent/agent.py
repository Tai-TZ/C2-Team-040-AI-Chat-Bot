"""VinWonders ReAct agent — Thought / Action / Observation loop."""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Generator, Optional

from src.core.llm_provider import LLMProvider
from src.prompts.vinwonders import build_agent_system_prompt
from src.telemetry.logger import logger
from src.agent.structured import build_chat_structured
from src.tools.registry import execute_tool

FINAL_ANSWER_RE = re.compile(
    r"Final Answer:\s*(.+)",
    re.IGNORECASE | re.DOTALL,
)
THOUGHT_RE = re.compile(r"Thought:\s*(.+?)(?=\n(?:Action:|Final Answer:)|\Z)", re.DOTALL | re.IGNORECASE)
ACTION_RE = re.compile(
    r"Action:\s*(\w+)\s*\((.*)\)",
    re.DOTALL | re.IGNORECASE,
)
ARG_RE = re.compile(r'(\w+)\s*=\s*["\']([^"\']*)["\']')


class ReActAgent:
    def __init__(
        self,
        llm: LLMProvider,
        tools: list[dict[str, Any]],
        max_steps: int = 8,
        tool_executor: Callable[[str, dict[str, Any]], str] | None = None,
    ):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self._execute = tool_executor or execute_tool
        self.trace: list[dict[str, Any]] = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            f"- {t['name']}: {t['description']}" for t in self.tools
        )
        return build_agent_system_prompt(tool_descriptions)

    def _build_prompt(self, user_input: str, steps: list[dict[str, str]]) -> str:
        parts = [f"Câu hỏi của khách: {user_input}\n"]
        if steps:
            parts.append("Các bước đã thực hiện:")
            for i, step in enumerate(steps, 1):
                parts.append(f"\n--- Bước {i} ---")
                parts.append(f"Thought: {step.get('thought', '')}")
                parts.append(f"Action: {step.get('action', '')}")
                parts.append(f"Observation: {step.get('observation', '')}")
        parts.append(
            "\nTiếp tục: đưa Thought + Action (một tool) HOẶC Thought + Final Answer nếu đã đủ dữ liệu."
        )
        return "\n".join(parts)

    @staticmethod
    def _parse_response(text: str) -> dict[str, Any]:
        text = text.strip()
        final = FINAL_ANSWER_RE.search(text)
        if final:
            thought = THOUGHT_RE.search(text)
            return {
                "type": "final",
                "thought": (thought.group(1).strip() if thought else ""),
                "answer": final.group(1).strip(),
            }

        action = ACTION_RE.search(text)
        thought = THOUGHT_RE.search(text)
        if action:
            name = action.group(1).strip()
            args_blob = action.group(2).strip()
            args: dict[str, str] = {}
            for match in ARG_RE.finditer(args_blob):
                args[match.group(1)] = match.group(2)
            return {
                "type": "action",
                "thought": (thought.group(1).strip() if thought else ""),
                "tool": name,
                "args": args,
                "action_line": f"{name}({args_blob})",
            }

        return {"type": "unparsed", "raw": text}

    def _execute_tool(self, tool_name: str, args: dict[str, Any]) -> str:
        logger.log_event("TOOL_CALL", {"tool": tool_name, "args": args})
        result = self._execute(tool_name, args)
        logger.log_event("TOOL_RESULT", {"tool": tool_name, "preview": result[:500]})
        return result

    def run(
        self,
        user_input: str,
        *,
        conversation_context: Optional[str] = None,
    ) -> str:
        self.trace = []
        if conversation_context:
            user_input = f"{conversation_context.strip()}\n\nCâu hỏi mới nhất: {user_input}"

        logger.log_event(
            "AGENT_START",
            {"input": user_input[:300], "model": self.llm.model_name},
        )

        system_prompt = self.get_system_prompt()
        steps: list[dict[str, str]] = []

        for step_idx in range(self.max_steps):
            prompt = self._build_prompt(user_input, steps)
            result = self.llm.generate(prompt, system_prompt=system_prompt)
            content = (result.get("content") or "").strip()
            logger.log_event(
                "AGENT_STEP",
                {
                    "step": step_idx + 1,
                    "latency_ms": result.get("latency_ms"),
                    "preview": content[:400],
                },
            )

            parsed = self._parse_response(content)

            if parsed["type"] == "final":
                self.trace.append(
                    {
                        "step": step_idx + 1,
                        "thought": parsed.get("thought"),
                        "final": True,
                    }
                )
                logger.log_event("AGENT_END", {"steps": step_idx + 1, "status": "final"})
                return parsed["answer"]

            if parsed["type"] == "action":
                tool = parsed["tool"]
                args = parsed.get("args") or {}
                observation = self._execute_tool(tool, args)
                steps.append(
                    {
                        "thought": parsed.get("thought", ""),
                        "action": parsed.get("action_line", tool),
                        "observation": observation,
                    }
                )
                self.trace.append(
                    {
                        "step": step_idx + 1,
                        "thought": parsed.get("thought"),
                        "action": parsed.get("action_line"),
                        "tool": tool,
                        "args": args,
                        "observation": observation[:800],
                    }
                )
                continue

            logger.log_event("AGENT_PARSE_ERROR", {"raw": content[:500]})
            steps.append(
                {
                    "thought": "parse error",
                    "action": "none",
                    "observation": (
                        "Không parse được output. Hãy trả đúng format "
                        "Thought / Action hoặc Final Answer."
                    ),
                }
            )

        logger.log_event("AGENT_END", {"steps": self.max_steps, "status": "max_steps"})
        return (
            "Mình đã tra cứu nhưng chưa hoàn tất trong số bước cho phép. "
            "Bạn thử hỏi lại với tên địa điểm và ngày cụ thể (vd: Nha Trang, 14-06-2026)."
        )

    def run_with_events(
        self,
        user_input: str,
        *,
        conversation_context: Optional[str] = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Yield trace events then final content for SSE streaming."""
        self.trace = []
        if conversation_context:
            user_input = f"{conversation_context.strip()}\n\nCâu hỏi mới nhất: {user_input}"

        system_prompt = self.get_system_prompt()
        steps: list[dict[str, str]] = []

        for step_idx in range(self.max_steps):
            prompt = self._build_prompt(user_input, steps)
            yield {
                "type": "trace",
                "message": f"Đang suy luận (bước {step_idx + 1})...",
            }

            result = self.llm.generate(prompt, system_prompt=system_prompt)
            content = (result.get("content") or "").strip()
            parsed = self._parse_response(content)

            if parsed["type"] == "final":
                yield {
                    "type": "trace",
                    "message": "Đang tổng hợp câu trả lời...",
                }
                structured = build_chat_structured(self.trace)
                if structured:
                    yield {"type": "structured", "data": structured}
                answer = parsed["answer"]
                chunk_size = 24
                for i in range(0, len(answer), chunk_size):
                    yield {
                        "type": "content",
                        "delta": answer[i : i + chunk_size],
                    }
                return

            if parsed["type"] == "action":
                tool = parsed["tool"]
                args = parsed.get("args") or {}
                yield {
                    "type": "trace",
                    "message": f"Đang gọi tool: {tool}...",
                }
                observation = self._execute_tool(tool, args)
                steps.append(
                    {
                        "thought": parsed.get("thought", ""),
                        "action": parsed.get("action_line", tool),
                        "observation": observation,
                    }
                )
                self.trace.append(
                    {
                        "step": step_idx + 1,
                        "thought": parsed.get("thought"),
                        "action": parsed.get("action_line"),
                        "tool": tool,
                        "args": args,
                        "observation": observation[:800],
                    }
                )
                continue

            steps.append(
                {
                    "thought": "parse error",
                    "action": "none",
                    "observation": "Format không hợp lệ, thử lại.",
                }
            )

        fallback = (
            "Mình chưa tra xong giá trong giới hạn bước. "
            "Bạn ghi rõ địa điểm + ngày (DD-MM-YYYY) để mình tra lại nhé."
        )
        for i in range(0, len(fallback), 24):
            yield {"type": "content", "delta": fallback[i : i + 24]}
