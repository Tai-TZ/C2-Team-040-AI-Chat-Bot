"""VinWonders ReAct agent — Thought / Action / Observation loop."""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Generator, Optional

from src.core.llm_provider import LLMProvider
from src.prompts.vinwonders import build_agent_system_prompt
from src.telemetry.logger import logger
from src.agent.dashboard import build_dashboard_after_tool, build_dashboard_from_trace
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

_TOOL_LABELS: dict[str, str] = {
    "resolve_site": "Xác định địa điểm VinWonders",
    "parse_visit_date": "Phân tích ngày đi",
    "get_weather_forecast": "Kiểm tra thời tiết (OpenWeatherMap)",
    "get_ticket_prices": "Tra cứu giá vé thật",
    "list_destinations": "Liệt kê điểm đến",
}


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
        self._progress_lines: list[str] = ["Khởi tạo VinWonders Tour Guide Agent..."]

    def _append_progress(self, line: str) -> None:
        if self._progress_lines and self._progress_lines[-1] == line:
            return
        self._progress_lines.append(line)

    def _line_for_tool_done(self, tool: str, observation: str) -> str:
        label = _TOOL_LABELS.get(tool, tool)
        try:
            data = json.loads(observation)
        except json.JSONDecodeError:
            return f"✓ Hoàn tất: {label}"
        if data.get("error"):
            return f"⚠ {label}: {str(data['error'])[:80]}"
        if tool == "resolve_site":
            return f"✓ Địa điểm: {data.get('siteName')} ({data.get('supplierCode')})"
        if tool == "parse_visit_date":
            return f"✓ Ngày đi: {data.get('usingDate')}"
        if tool == "get_weather_forecast":
            rain = "có mưa" if data.get("hasRain") else "không mưa"
            return (
                f"✓ Thời tiết {data.get('location')}: {data.get('tempC')}°C, "
                f"{data.get('description')} ({rain})"
            )
        if tool == "get_ticket_prices":
            cheapest = data.get("cheapestFormatted") or "—"
            return f"✓ Giá rẻ nhất: {cheapest} ({data.get('ticketCount', 0)} loại vé)"
        return f"✓ Hoàn tất: {label}"

    def _trace_event(self, message: str) -> dict[str, Any]:
        step_count = len(self.trace)
        progress = min(12 + step_count * 14, 92)
        return {
            "type": "trace",
            "message": message,
            "lines": list(self._progress_lines),
            "progress": progress,
            "step": step_count + 1,
        }

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
        self._progress_lines = ["Khởi tạo VinWonders Tour Guide Agent..."]
        if conversation_context:
            user_input = f"{conversation_context.strip()}\n\nCâu hỏi mới nhất: {user_input}"

        system_prompt = self.get_system_prompt()
        steps: list[dict[str, str]] = []

        for step_idx in range(self.max_steps):
            prompt = self._build_prompt(user_input, steps)
            think_msg = f"Đang suy luận (bước {step_idx + 1})..."
            self._append_progress(think_msg)
            yield self._trace_event(think_msg)

            result = self.llm.generate(prompt, system_prompt=system_prompt)
            content = (result.get("content") or "").strip()
            parsed = self._parse_response(content)

            if parsed["type"] == "final":
                done_msg = "Đang tổng hợp câu trả lời cho bạn..."
                self._append_progress(done_msg)
                yield self._trace_event(done_msg)
                structured = build_chat_structured(self.trace)
                if structured:
                    yield {"type": "structured", "data": structured}
                dashboard = build_dashboard_from_trace(self.trace)
                if dashboard:
                    yield {"type": "dashboard", "data": dashboard}
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
                trace_msg = {
                    "get_weather_forecast": "Đang kiểm tra thời tiết tại điểm đến...",
                    "get_ticket_prices": "Đang crawl giá vé VinWonders (API)...",
                    "resolve_site": "Đang xác định mã địa điểm...",
                    "parse_visit_date": "Đang phân tích ngày đi...",
                    "list_destinations": "Đang tải danh sách điểm đến...",
                }.get(tool, f"Đang chạy tool {tool}...")
                self._append_progress(trace_msg)
                yield self._trace_event(trace_msg)
                observation = self._execute_tool(tool, args)
                self._append_progress(self._line_for_tool_done(tool, observation))
                done_status = {
                    "get_weather_forecast": "Đã kiểm tra thời tiết",
                    "get_ticket_prices": "Đã lấy giá vé",
                    "resolve_site": "Đã xác định địa điểm",
                    "parse_visit_date": "Đã xác định ngày đi",
                    "list_destinations": "Đã tải danh sách điểm đến",
                }.get(tool, f"Đã hoàn tất {tool}")
                yield self._trace_event(done_status)
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
                dashboard = build_dashboard_after_tool(tool, observation, self.trace)
                if dashboard:
                    yield {"type": "dashboard", "data": dashboard}
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
