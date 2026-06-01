import ast
import re
from typing import Any, Dict, List, Optional, Tuple

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class ReActAgent:
    """ReAct agent: Thought -> Action -> Observation loop until Final Answer."""

    PROMPT_V1 = "v1"
    PROMPT_V2 = "v2"

    def __init__(
        self,
        llm: LLMProvider,
        tools: List[Dict[str, Any]],
        max_steps: int = 5,
        prompt_version: str = "v2",
    ):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.prompt_version = prompt_version
        self.history: List[str] = []
        self._tool_map = {t["name"]: t for t in tools}

    def get_system_prompt(self) -> str:
        tool_lines = "\n".join(
            f"- {t['name']}({', '.join(t.get('params', []))}): {t['description']}"
            for t in self.tools
        )

        base = f"""You are a smart e-commerce assistant with access to these tools:
{tool_lines}

You MUST solve multi-step problems by calling tools one at a time.
Do NOT invent prices, stock, or discounts — always use tools.

Output format (strict — one block per step):
Thought: <your reasoning>
Action: tool_name(arg1, arg2)
OR when done:
Thought: <summary>
Final Answer: <complete answer for the user>
"""

        if self.prompt_version == self.PROMPT_V1:
            return base

        # v2: fewer parse errors, explicit examples and guardrails
        return base + """
Rules (v2):
1. Use lowercase for item names (iphone) and destinations (hanoi).
2. Use UPPERCASE for coupon codes (WINNER).
3. Call ONE tool per step. Wait for Observation before the next Action.
4. Do NOT wrap Action in markdown or JSON — raw format only.
5. For total price: first check_stock, then get_discount, calc_shipping, then calc_total.

Example:
User: Buy 2 iPhones with WINNER coupon, ship to Hanoi.
Thought: I need the iPhone price and stock first.
Action: check_stock(iphone)
Observation: iPhone 15: price=$999.0, stock=50 units, weight=0.2kg
Thought: Now get the WINNER coupon discount.
Action: get_discount(WINNER)
...
Final Answer: Your total for 2 iPhones with 15% off and Hanoi shipping is $X.
"""

    def run(self, user_input: str) -> str:
        logger.log_event(
            "AGENT_START",
            {"input": user_input, "model": self.llm.model_name, "prompt_version": self.prompt_version},
        )

        self.history = [f"User: {user_input}"]
        steps = 0
        final_answer: Optional[str] = None

        while steps < self.max_steps:
            prompt = "\n".join(self.history)
            result = self.llm.generate(prompt, system_prompt=self.get_system_prompt())
            content = result["content"]

            tracker.track_request(
                provider=result.get("provider", "unknown"),
                model=self.llm.model_name,
                usage=result["usage"],
                latency_ms=result["latency_ms"],
            )

            logger.log_event("AGENT_STEP", {"step": steps + 1, "llm_output": content[:500]})

            final = self._extract_final_answer(content)
            if final:
                final_answer = final
                self.history.append(content)
                break

            action = self._extract_action(content)
            if not action:
                logger.log_event("AGENT_ERROR", {"type": "PARSE_ERROR", "step": steps + 1})
                self.history.append(content)
                self.history.append(
                    "Observation: Error — could not parse Action. "
                    "Use format: Action: tool_name(arg1, arg2)"
                )
                steps += 1
                continue

            tool_name, args = action
            observation = self._execute_tool(tool_name, args)
            logger.log_event(
                "TOOL_CALL",
                {"tool": tool_name, "args": args, "observation": observation},
            )

            self.history.append(content)
            self.history.append(f"Observation: {observation}")
            steps += 1

        if final_answer is None:
            logger.log_event("AGENT_ERROR", {"type": "MAX_STEPS", "steps": steps})
            final_answer = (
                f"Could not complete within {self.max_steps} steps. "
                f"Last state: {self.history[-1][:200]}"
            )

        logger.log_event("AGENT_END", {"steps": steps, "success": final_answer is not None})
        return final_answer

    def get_reasoning_steps(self) -> List[str]:
        """Extract Thought lines from conversation history for UI display."""
        steps: List[str] = []
        for entry in self.history:
            for match in re.finditer(r"Thought:\s*(.+?)(?:\n|$)", entry, re.IGNORECASE):
                thought = match.group(1).strip()
                if thought and thought not in steps:
                    steps.append(thought)
        return steps

    def _extract_final_answer(self, text: str) -> Optional[str]:
        match = re.search(r"Final Answer:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None

    def _extract_action(self, text: str) -> Optional[Tuple[str, str]]:
        match = re.search(r"Action:\s*(\w+)\((.*)\)", text, re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        return match.group(1).strip(), match.group(2).strip()

    def _parse_args(self, args_str: str) -> List[Any]:
        if not args_str.strip():
            return []
        # Strip quotes from bare words: iphone -> "iphone"
        normalized = re.sub(
            r"(?<=[\(,\s])([a-zA-Z_]\w*)(?=[,\)])",
            lambda m: f'"{m.group(1)}"' if not m.group(1).replace(".", "").isdigit() else m.group(1),
            args_str,
        )
        try:
            parsed = ast.literal_eval(f"({normalized},)" if "," not in normalized else f"({normalized})")
            return list(parsed) if isinstance(parsed, tuple) else [parsed]
        except (SyntaxError, ValueError):
            return [a.strip().strip("'\"") for a in args_str.split(",")]

    def _execute_tool(self, tool_name: str, args_str: str) -> str:
        tool_name = tool_name.strip()
        if tool_name not in self._tool_map:
            logger.log_event("AGENT_ERROR", {"type": "HALLUCINATION", "tool": tool_name})
            available = ", ".join(self._tool_map.keys())
            return f"Error: Tool '{tool_name}' not found. Available: {available}"

        tool = self._tool_map[tool_name]
        func = tool["func"]
        try:
            args = self._parse_args(args_str)
            return str(func(*args))
        except TypeError as e:
            logger.log_event("AGENT_ERROR", {"type": "INVALID_ARGS", "tool": tool_name, "error": str(e)})
            expected = ", ".join(tool.get("params", []))
            return f"Error: Invalid arguments for {tool_name}. Expected: ({expected}). Details: {e}"
        except Exception as e:
            logger.log_event("AGENT_ERROR", {"type": "TOOL_ERROR", "tool": tool_name, "error": str(e)})
            return f"Error executing {tool_name}: {e}"
