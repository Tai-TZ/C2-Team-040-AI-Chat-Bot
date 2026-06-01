"""VinWonders ReAct agent — Thought / Action / Observation loop."""

from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Generator, Optional

from src.core.llm_provider import LLMProvider
from src.agent.guardrails import reject_premature_final
from src.prompts.vinwonders import build_agent_system_prompt, build_agent_system_prompt_v1
from src.telemetry.logger import logger
from src.agent.bootstrap import run_bootstrap_pipeline
from src.agent.dashboard import build_dashboard_after_tool, build_dashboard_from_trace
from src.agent.structured import (
    build_chat_structured,
    build_fallback_answer,
    ensure_followup_question,
    finalize_structured_payload,
)
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

_TRAVEL_HINTS = (
    "vé",
    "vinwonders",
    "đi chơi",
    "du lịch",
    "nha trang",
    "phú quốc",
    "hà nội",
    "đà nẵng",
    "ngày mai",
    "cuối tuần",
    "thời tiết",
    "giá",
    "combo",
    "công viên",
    "thủy cung",
    "check",
    "xem thử",
    "bao nhiêu",
)

_OFF_TOPIC_HINTS = (
    "python",
    "javascript",
    "code",
    "bài tập",
    "homework",
    "toán",
    "crypto",
    "bitcoin",
    "chính trị",
    "bầu cử",
    "y tế",
    "thuốc",
    "luật",
    "lập trình",
)


class ReActAgent:
    def __init__(
        self,
        llm: LLMProvider,
        tools: list[dict[str, Any]],
        max_steps: int = 8,
        tool_executor: Callable[[str, dict[str, Any]], str] | None = None,
        *,
        prompt_version: str = "v2",
    ):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.prompt_version = prompt_version
        self.enable_bootstrap = prompt_version == "v2"
        self.enable_guards = prompt_version == "v2"
        self._execute = tool_executor or execute_tool
        self.trace: list[dict[str, Any]] = []
        self._ui_steps: list[dict[str, Any]] = []
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

    @staticmethod
    def _summarize_for_ui(text: str, max_len: int = 110) -> str:
        line = re.sub(r"\s+", " ", text.strip())
        if len(line) <= max_len:
            return line
        return line[: max_len - 1] + "…"

    def _tool_action_detail(self, tool: str, args: dict[str, Any]) -> str:
        label = _TOOL_LABELS.get(tool, tool)
        if tool == "resolve_site":
            q = args.get("query") or args.get("location") or ""
            return f"Xác định địa điểm: {q}" if q else label
        if tool == "parse_visit_date":
            d = args.get("date_text") or args.get("date") or ""
            return f"Phân tích ngày: {d}" if d else label
        if tool == "get_weather_forecast":
            loc = args.get("location") or ""
            d = args.get("using_date") or args.get("usingDate") or ""
            if loc and d:
                return f"Kiểm tra thời tiết {loc} · {d}"
            return f"Kiểm tra thời tiết {loc}" if loc else label
        if tool == "get_ticket_prices":
            code = args.get("supplier_code") or args.get("supplierCode") or ""
            d = args.get("using_date") or args.get("usingDate") or ""
            if code and d:
                return f"Tra giá vé {code} · {d}"
            return label
        return label

    def _reasoning_from_parsed(self, parsed: dict[str, Any]) -> tuple[str, list[str]]:
        """Map model Thought/Action to user-facing loading lines."""
        lines: list[str] = []
        thought = (parsed.get("thought") or "").strip()
        if thought:
            lines.append(f"💭 {self._summarize_for_ui(thought)}")

        status = "Đang phân tích bước tiếp theo..."
        if parsed["type"] == "action":
            tool = parsed["tool"]
            args = parsed.get("args") or {}
            detail = self._tool_action_detail(tool, args)
            lines.append(f"→ {detail}")
            status = detail
        elif parsed["type"] == "final":
            status = "Đang soạn câu trả lời..."
        elif parsed["type"] == "unparsed":
            status = "Đang điều chỉnh phản hồi từ model..."
        return status, lines

    def _compute_progress(self) -> int:
        tools_done = [t.get("tool") for t in self.trace if t.get("tool")]
        if any(t.get("final") for t in self.trace):
            return 95
        if "get_ticket_prices" in tools_done:
            return 82
        if "get_weather_forecast" in tools_done:
            return 62
        if "parse_visit_date" in tools_done:
            return 45
        if "resolve_site" in tools_done:
            return 28
        return min(10 + len(self._progress_lines) * 4, 24)

    @staticmethod
    def _observation_preview(observation: str, max_len: int = 220) -> str:
        try:
            data = json.loads(observation)
            if data.get("error"):
                return f"Lỗi: {data['error']}"[:max_len]
            if "cheapestFormatted" in data:
                return (
                    f"{data.get('siteName', '')} · {data.get('usingDate', '')} · "
                    f"rẻ nhất {data.get('cheapestFormatted', '—')}"
                )[:max_len]
            if "tempC" in data:
                return (
                    f"{data.get('location', '')} {data.get('usingDate', '')}: "
                    f"{data.get('description', '')} {data.get('tempC', '')}°C"
                )[:max_len]
            if "supplierCode" in data:
                return (
                    f"{data.get('siteName', data.get('region', ''))} "
                    f"→ {data.get('supplierCode', '')}"
                )[:max_len]
            if "usingDate" in data:
                return f"Ngày đi: {data.get('usingDate', '')}"[:max_len]
        except json.JSONDecodeError:
            pass
        line = observation.replace("\n", " ").strip()
        return line[:max_len] + ("…" if len(line) > max_len else "")

    def _agent_step(
        self,
        *,
        phase: str,
        title: str,
        detail: str = "",
        tool: str | None = None,
        args: dict[str, Any] | None = None,
        observation_preview: str = "",
        status: str = "done",
        source: str = "model",
    ) -> dict[str, Any]:
        rec = {
            "id": f"step-{len(self._ui_steps) + 1}-{int(time.time() * 1000)}",
            "phase": phase,
            "title": title,
            "detail": detail,
            "tool": tool,
            "args": {k: str(v) for k, v in (args or {}).items()},
            "observationPreview": observation_preview,
            "status": status,
            "source": source,
        }
        self._ui_steps.append(rec)
        return {"type": "agent_step", "step": rec}

    def _agent_done_event(self) -> dict[str, Any]:
        tools = [t for t in self.trace if t.get("tool")]
        return {
            "type": "agent_done",
            "run": {
                "steps": list(self._ui_steps),
                "toolCount": len(tools),
                "reactSteps": len(self.trace),
            },
        }

    def _trace_event(
        self, message: str, *, phase: str | None = None
    ) -> dict[str, Any]:
        step_count = len(self.trace)
        progress = self._compute_progress()
        if phase == "reasoning":
            progress = max(progress, min(18 + step_count * 8, 40))
        elif phase == "tool":
            progress = max(progress, min(35 + step_count * 12, 85))
        evt: dict[str, Any] = {
            "type": "trace",
            "message": message,
            "lines": list(self._progress_lines),
            "progress": progress,
            "step": step_count + 1,
        }
        if phase:
            evt["phase"] = phase
        return evt

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            f"- {t['name']}: {t['description']}" for t in self.tools
        )
        if self.prompt_version == "v1":
            return build_agent_system_prompt_v1(tool_descriptions)
        return build_agent_system_prompt(tool_descriptions)

    @staticmethod
    def _is_travel_intent(text: str) -> bool:
        t = text.lower()
        return any(h in t for h in _TRAVEL_HINTS)

    @staticmethod
    def _is_off_topic(text: str) -> bool:
        t = text.lower()
        if ReActAgent._is_travel_intent(text):
            return False
        return any(h in t for h in _OFF_TOPIC_HINTS)

    @staticmethod
    def _requires_full_pipeline(text: str) -> bool:
        """Price/weather trip questions must run all core tools."""
        t = text.lower()
        if not ReActAgent._is_travel_intent(text):
            return False
        return any(
            x in t
            for x in (
                "giá",
                "vé",
                "check",
                "xem",
                "thời tiết",
                "cuối tuần",
                "đi chơi",
                "bao nhiêu",
                "toàn bộ",
                "m check",
            )
        )

    def _tools_used(self) -> set[str]:
        return {row.get("tool") for row in self.trace if row.get("tool")}

    def _pipeline_complete(self) -> bool:
        used = self._tools_used()
        return "get_weather_forecast" in used and "get_ticket_prices" in used

    def _reject_premature_final(self, user_input: str) -> str | None:
        if not self.enable_guards:
            return None
        if self._is_off_topic(user_input):
            return None
        if not self._requires_full_pipeline(user_input):
            return None
        return reject_premature_final(
            self.trace,
            requires_pipeline=True,
        )

    @staticmethod
    def _observation_for_prompt(tool: str, observation: str, *, max_len: int = 1800) -> str:
        """Shrink tool JSON so later LLM calls stay within DS2API limits."""
        try:
            data = json.loads(observation)
        except json.JSONDecodeError:
            return observation[:max_len]

        if tool == "get_ticket_prices":
            tickets = data.get("tickets") or []
            slim_tickets = [
                {
                    "name": t.get("name"),
                    "salePrice": t.get("salePrice"),
                    "originalPrice": t.get("originalPrice"),
                }
                for t in tickets[:5]
            ]
            data = {
                "supplierCode": data.get("supplierCode"),
                "usingDate": data.get("usingDate"),
                "siteName": data.get("siteName"),
                "ticketCount": data.get("ticketCount"),
                "cheapestFormatted": data.get("cheapestFormatted"),
                "cheapestTicketName": data.get("cheapestTicketName"),
                "tickets": slim_tickets,
            }
        elif tool == "get_weather_forecast":
            keep = (
                "location",
                "usingDate",
                "tempC",
                "description",
                "hasRain",
                "rainRisk",
                "popPercent",
                "recommendation",
                "suggestReschedule",
            )
            data = {k: data[k] for k in keep if k in data}

        text = json.dumps(data, ensure_ascii=False)
        return text[:max_len]

    def _build_prompt(self, user_input: str, steps: list[dict[str, str]]) -> str:
        parts = [f"Câu hỏi của khách: {user_input}\n"]
        if steps:
            parts.append("Các bước đã thực hiện:")
            for i, step in enumerate(steps, 1):
                parts.append(f"\n--- Bước {i} ---")
                parts.append(f"Thought: {step.get('thought', '')[:400]}")
                parts.append(f"Action: {step.get('action', '')}")
                obs = step.get("observation", "")
                parts.append(f"Observation: {obs}")
        parts.append(
            "\nTiếp tục: đưa Thought + Action (một tool) HOẶC Thought + Final Answer nếu đã đủ dữ liệu."
        )
        return "\n".join(parts)

    def _yield_pre_answer_ui(self) -> Generator[dict[str, Any], None, None]:
        """Structured cards + dashboard before streamed text."""
        yield self._agent_step(
            phase="summarize",
            title="Final Answer",
            detail="Karphany đang stream câu trả lời từ Observation",
            status="running",
            source="system",
        )
        structured = finalize_structured_payload(self.trace)
        if structured.get("actions") or structured.get("weather") or structured.get(
            "priceQuote"
        ) or structured.get("destinationMap"):
            yield {"type": "structured", "data": structured}
        dashboard = build_dashboard_from_trace(self.trace)
        if dashboard:
            yield {"type": "dashboard", "data": dashboard}

    def _yield_text_deltas(self, text: str) -> Generator[dict[str, Any], None, None]:
        """Emit answer text as SSE content chunks (fallback when not LLM-streaming)."""
        if not text:
            return
        for part in re.findall(r"\S+\s*|\n", text):
            yield {"type": "content", "delta": part}

    def _stream_answer_events(self, answer: str) -> Generator[dict[str, Any], None, None]:
        answer = ensure_followup_question(answer)
        yield from self._yield_pre_answer_ui()
        yield from self._yield_text_deltas(answer)
        if self._ui_steps and self._ui_steps[-1].get("phase") == "summarize":
            self._ui_steps[-1]["status"] = "done"
            yield {"type": "agent_step", "step": self._ui_steps[-1]}
        yield self._agent_done_event()

    def _generate_final_streamed(
        self,
        prompt: str,
        system_prompt: str,
        *,
        steps: list[dict[str, str]],
    ) -> Generator[dict[str, Any], None, None]:
        """Stream Final Answer tokens live from LLM (OpenRouter / OpenAI-compatible)."""
        yield from self._yield_pre_answer_ui()

        buffer = ""
        final_start: int | None = None
        emitted = 0
        marker = re.compile(r"Final Answer:\s*", re.IGNORECASE)

        try:
            for delta in self.llm.stream(prompt, system_prompt=system_prompt):
                if not delta:
                    continue
                buffer += delta
                if final_start is None:
                    m = marker.search(buffer)
                    if m:
                        final_start = m.end()
                if final_start is not None:
                    answer_part = buffer[final_start:]
                    if len(answer_part) > emitted:
                        chunk = answer_part[emitted:]
                        emitted = len(answer_part)
                        yield {"type": "content", "delta": chunk}
        except Exception as exc:
            logger.log_event("LLM_STREAM_ERROR", {"error": str(exc)})
            fallback = build_fallback_answer(self.trace) or (
                "Mình tạm không stream được câu trả lời. Bạn thử hỏi lại sau vài giây nhé."
            )
            yield from self._yield_text_deltas(ensure_followup_question(fallback))
            yield self._agent_done_event()
            return

        parsed = self._parse_response(buffer)
        if parsed["type"] == "final":
            self.trace.append(
                {
                    "step": len(self.trace) + 1,
                    "thought": parsed.get("thought"),
                    "final": True,
                }
            )
            raw_answer = parsed["answer"]
            full_answer = ensure_followup_question(raw_answer)
            if final_start is None:
                yield from self._yield_text_deltas(full_answer)
            else:
                if emitted < len(raw_answer):
                    yield from self._yield_text_deltas(raw_answer[emitted:])
                suffix = full_answer[len(raw_answer) :]
                if suffix.strip():
                    yield from self._yield_text_deltas(suffix)
        else:
            fallback = build_fallback_answer(self.trace)
            if fallback:
                yield from self._yield_text_deltas(fallback)
            else:
                yield from self._yield_text_deltas(
                    "Mình đã tra cứu xong dữ liệu. Bạn muốn đặt vé hay đổi ngày khác không?"
                )

        if self._ui_steps and self._ui_steps[-1].get("phase") == "summarize":
            self._ui_steps[-1]["status"] = "done"
            yield {"type": "agent_step", "step": self._ui_steps[-1]}
        yield self._agent_done_event()

    def _yield_tool_completed(
        self,
        tool: str,
        args: dict[str, Any],
        observation: str,
        steps: list[dict[str, str]],
        *,
        thought: str = "",
        action_line: str | None = None,
        source: str = "model",
    ) -> Generator[dict[str, Any], None, None]:
        trace_msg = self._tool_action_detail(tool, args)
        yield self._agent_step(
            phase="tool",
            title=f"Action: {tool}",
            detail=trace_msg,
            tool=tool,
            args=args,
            status="running",
            source=source,
        )
        self._append_progress(f"⚙ {trace_msg}")
        yield self._trace_event(trace_msg, phase="tool")
        done_line = self._line_for_tool_done(tool, observation)
        preview = self._observation_preview(observation)
        yield self._agent_step(
            phase="tool",
            title=f"Observation: {tool}",
            detail=done_line.replace("✓ ", ""),
            tool=tool,
            args=args,
            observation_preview=preview,
            status="done" if '"error"' not in observation[:80] else "error",
            source=source,
        )
        self._append_progress(done_line)
        yield self._trace_event(done_line.replace("✓ ", "", 1), phase="tool")

        prompt_obs = self._observation_for_prompt(tool, observation)
        line = action_line or f"{tool}({args})"
        steps.append(
            {
                "thought": thought,
                "action": line,
                "observation": prompt_obs,
                "tool": tool,
            }
        )
        self.trace.append(
            {
                "step": len(self.trace) + 1,
                "thought": thought,
                "action": line,
                "tool": tool,
                "args": args,
                "observation": observation[:800],
            }
        )
        dashboard = build_dashboard_after_tool(tool, observation, self.trace)
        if dashboard:
            yield {"type": "dashboard", "data": dashboard}
        if tool in ("get_weather_forecast", "get_ticket_prices"):
            structured = finalize_structured_payload(self.trace)
            if structured:
                yield {"type": "structured", "data": structured}

    def _finish_from_trace_fallback(
        self, user_input: str
    ) -> Generator[dict[str, Any], None, bool]:
        """If tools already ran, answer from trace instead of failing the chat."""
        answer = build_fallback_answer(self.trace, user_input=user_input)
        if not answer:
            return False
        warn = (
            "\n\n_(AI tạm lỗi khi soạn câu trả lời; nội dung trên tổng hợp từ dữ liệu "
            "thời tiết & giá vé đã tra cứu.)_"
        )
        self._append_progress("✓ Tổng hợp câu trả lời từ dữ liệu đã tra")
        yield self._trace_event("Đã tổng hợp từ kết quả tra cứu", phase="summarize")
        yield from self._stream_answer_events(answer + warn)
        return True

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

        if self.enable_bootstrap and self._requires_full_pipeline(user_input):

            def _bootstrap_done(
                tool: str, action_line: str, observation: str, args: dict[str, Any]
            ):
                steps.append(
                    {
                        "thought": "bootstrap",
                        "action": action_line,
                        "observation": observation,
                    }
                )
                self.trace.append(
                    {
                        "tool": tool,
                        "args": args,
                        "observation": observation[:800],
                    }
                )
                return iter(())

            for _ in run_bootstrap_pipeline(
                user_input,
                self.trace,
                execute_tool=self._execute_tool,
                tools_used=self._tools_used,
                on_tool_done=_bootstrap_done,
            ):
                pass

            if self._pipeline_complete():
                prompt = self._build_prompt(user_input, steps)
                result = self.llm.generate(prompt, system_prompt=system_prompt)
                content = (result.get("content") or "").strip()
                parsed = self._parse_response(content)
                if parsed["type"] == "final" and parsed.get("answer"):
                    logger.log_event("AGENT_END", {"steps": 0, "status": "bootstrap_final"})
                    return ensure_followup_question(parsed["answer"])

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
                reject = self._reject_premature_final(user_input)
                if reject:
                    steps.append(
                        {
                            "thought": parsed.get("thought", ""),
                            "action": "none",
                            "observation": reject,
                        }
                    )
                    continue
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

            reject = self._reject_premature_final(user_input)
            obs = reject or (
                "Không parse được output. Bắt buộc format:\n"
                "Thought: ...\nAction: tool(...) HOẶC Final Answer: ... "
                "(chỉ Final Answer sau khi đã gọi đủ tool)."
            )
            logger.log_event("AGENT_PARSE_ERROR", {"raw": content[:500]})
            steps.append(
                {
                    "thought": "parse error",
                    "action": "none",
                    "observation": obs,
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
        self._ui_steps = []
        self._progress_lines = ["Khởi tạo VinWonders Tour Guide Agent..."]
        yield self._agent_step(
            phase="init",
            title="Khởi động ReAct Agent",
            detail="Karphany · VinWonders Tour Guide",
            status="done",
            source="system",
        )
        yield self._trace_event("Đã nhận câu hỏi — khởi động agent...", phase="init")
        if conversation_context:
            user_input = f"{conversation_context.strip()}\n\nCâu hỏi mới nhất: {user_input}"

        system_prompt = self.get_system_prompt()
        steps: list[dict[str, str]] = []

        if self.enable_bootstrap and self._requires_full_pipeline(user_input):

            def _on_bootstrap_tool(
                tool: str, action_line: str, observation: str, args: dict[str, Any]
            ) -> Generator[dict[str, Any], None, None]:
                yield from self._yield_tool_completed(
                    tool,
                    args,
                    observation,
                    steps,
                    thought="Karphany đang tra cứu dữ liệu thật...",
                    action_line=action_line,
                    source="bootstrap",
                )

            yield self._agent_step(
                phase="tool",
                title="Auto pipeline",
                detail="resolve_site → parse_visit_date → weather → prices",
                status="done",
                source="bootstrap",
            )
            yield self._trace_event(
                "Đang tra cứu địa điểm, ngày, thời tiết và giá vé...", phase="tool"
            )
            yield from run_bootstrap_pipeline(
                user_input,
                self.trace,
                execute_tool=self._execute_tool,
                tools_used=self._tools_used,
                on_tool_done=_on_bootstrap_tool,
            )

        if self._pipeline_complete() and self._requires_full_pipeline(user_input):
            prompt = self._build_prompt(user_input, steps)
            yield self._trace_event("Đang stream câu trả lời từ OpenRouter...", phase="summarize")
            yield from self._generate_final_streamed(
                prompt, system_prompt, steps=steps
            )
            return

        for step_idx in range(self.max_steps):
            prompt = self._build_prompt(user_input, steps)
            think_msg = f"Đang suy luận (bước {step_idx + 1})..."
            yield self._agent_step(
                phase="reasoning",
                title=think_msg,
                detail="LLM đọc Observation và chọn Action hoặc Final Answer",
                status="running",
                source="model",
            )
            yield self._trace_event(think_msg, phase="reasoning")

            try:
                result = self.llm.generate(prompt, system_prompt=system_prompt)
            except Exception as exc:
                logger.log_event("LLM_ERROR", {"step": step_idx + 1, "error": str(exc)})
                finished = yield from self._finish_from_trace_fallback(user_input)
                if finished:
                    return
                raise

            content = (result.get("content") or "").strip()
            parsed = self._parse_response(content)

            reason_status, reason_lines = self._reasoning_from_parsed(parsed)
            for line in reason_lines:
                self._append_progress(line)
            yield self._trace_event(reason_status, phase="reasoning")
            if self._ui_steps and self._ui_steps[-1].get("phase") == "reasoning":
                self._ui_steps[-1]["status"] = "done"
                yield {"type": "agent_step", "step": self._ui_steps[-1]}

            thought = (parsed.get("thought") or "").strip()
            if thought:
                yield self._agent_step(
                    phase="react",
                    title="Thought",
                    detail=self._summarize_for_ui(thought, 180),
                    status="done",
                    source="model",
                )

            if parsed["type"] == "final":
                reject = self._reject_premature_final(user_input)
                if reject:
                    steps.append(
                        {
                            "thought": parsed.get("thought", ""),
                            "action": "none",
                            "observation": reject,
                        }
                    )
                    yield self._trace_event(
                        "Karphany cần tra cứu thêm dữ liệu...",
                        phase="reasoning",
                    )
                    continue
                done_msg = "Đang stream câu trả lời cho bạn..."
                self._append_progress(done_msg)
                yield self._trace_event(done_msg, phase="summarize")
                prompt_final = self._build_prompt(user_input, steps)
                yield from self._generate_final_streamed(
                    prompt_final, system_prompt, steps=steps
                )
                return

            if parsed["type"] == "action":
                tool = parsed["tool"]
                args = parsed.get("args") or {}
                observation = self._execute_tool(tool, args)
                yield from self._yield_tool_completed(
                    tool,
                    args,
                    observation,
                    steps,
                    thought=parsed.get("thought", ""),
                    action_line=parsed.get("action_line", tool),
                    source="model",
                )
                continue

            reject = self._reject_premature_final(user_input)
            steps.append(
                {
                    "thought": "parse error",
                    "action": "none",
                    "observation": reject
                    or (
                        "Format không hợp lệ. Dùng Thought + Action hoặc "
                        "Thought + Final Answer (sau khi đã gọi tool)."
                    ),
                }
            )
            yield self._trace_event("Đang điều chỉnh theo quy trình Karphany...", phase="reasoning")
            continue

        finished = yield from self._finish_from_trace_fallback(user_input)
        if finished:
            return
        fallback = (
            "Mình chưa tra xong trong giới hạn bước. "
            "Bạn thử lại: «Nha Trang cuối tuần sau, check thời tiết và giá vé»."
        )
        yield self._agent_done_event()
        for i in range(0, len(fallback), 24):
            yield {"type": "content", "delta": fallback[i : i + 24]}
