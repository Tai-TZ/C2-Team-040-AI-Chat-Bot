"""Quick DS2API probe with agent-sized prompts."""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

from src.llm import ds2api
from src.prompts.vinwonders import build_agent_system_prompt
from src.tools.registry import VINWONDERS_TOOLS

tools = "\n".join(f"- {t['name']}: {t['description']}" for t in VINWONDERS_TOOLS)
sp = build_agent_system_prompt(tools)
print("system chars:", len(sp))

user_q = "Ngày mai Hà Nội có gì chơi không?"
cases = [
    ("full-system", [{"role": "system", "content": sp}, {"role": "user", "content": user_q}]),
    ("short-system", [{"role": "system", "content": "VinWonders agent. Reply in Vietnamese."}, {"role": "user", "content": user_q}]),
    ("user-only-merged", [{"role": "user", "content": sp[:1500] + "\n\n" + user_q}]),
]
for label, msgs in cases:
    try:
        r = ds2api.chat_completion(msgs, model="deepseek-v4-flash", timeout=90)
        print(label, "OK", ds2api.extract_assistant_text(r)[:50])
    except Exception as e:
        print(label, "FAIL", str(e)[:150])
