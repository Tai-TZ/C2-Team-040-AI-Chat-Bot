# Lab 3: Chatbot vs ReAct Agent (Industry Edition)

Welcome to Phase 3 of the Agentic AI course! This lab focuses on moving from a simple LLM Chatbot to a sophisticated **ReAct Agent** with industry-standard monitoring.

## 🚀 Getting Started

### 1. Setup Environment
Copy the `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Directory Structure
- `src/tools/`: Extension point for your custom tools.

## 🏠 Running with Local Models (CPU)

If you don't want to use OpenAI or Gemini, you can run open-source models (like Phi-3) directly on your CPU using `llama-cpp-python`.

### 1. Download the Model
Download the **Phi-3-mini-4k-instruct-q4.gguf** (approx 2.2GB) from Hugging Face:
- [Phi-3-mini-4k-instruct-GGUF](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf)
- Direct Download: [phi-3-mini-4k-instruct-q4.gguf](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf)

### 2. Place Model in Project
Create a `models/` folder in the root and move the downloaded `.gguf` file there.

### 3. Update `.env`
Change your `DEFAULT_PROVIDER` and set the path:
```env
DEFAULT_PROVIDER=local
LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
```

## 🎯 Lab Objectives

1.  **Baseline Chatbot**: Observe the limitations of a standard LLM when faced with multi-step reasoning.
2.  **ReAct Loop**: Implement the `Thought-Action-Observation` cycle in `src/agent/agent.py`.
3.  **Provider Switching**: Swap between OpenAI and Gemini seamlessly using the `LLMProvider` interface.
4.  **Failure Analysis**: Use the structured logs in `logs/` to identify why the agent fails (hallucinations, parsing errors).
5.  **Grading & Bonus**: Follow [SCORING.md](./SCORING.md). Submit [`report/group_report/GROUP_REPORT_C2-Team-040.md`](./report/group_report/GROUP_REPORT_C2-Team-040.md).

### Lab 3 quick commands (VinWonders)

```bash
python chatbot.py "Nha Trang cuối tuần sau giá bao nhiêu?"   # baseline
python run_agent.py "Nha Trang cuối tuần sau" --version v2   # ReAct agent
python main.py compare                                        # chatbot vs v1 vs v2
python scripts/eval_lab3.py --offline                         # scoring checks
python -m pytest tests/test_vinwonders_scoring.py -q
```

## 🛠️ How to Use This Baseline
The code is designed as a **Production Prototype**. It includes:
- **Telemetry**: Every action is logged in JSON format for later analysis.
- **Robust Provider Pattern**: Easily extendable to any LLM API.
- **Clean Skeletons**: Focus on the logic that matters—the agent's reasoning process.

---

## VinWonders web app (giá vé + chat AI)

### 1. Cấu hình môi trường

```bash
cp .env.example .env
```

Chỉnh `.env`:

```env
DS2API_BASE_URL=https://deep-seek-api-kappa.vercel.app
DS2API_API_KEY=<api-key-cua-ban>
DS2API_MODEL=deepseek-v4-flash
```

DS2API gateway (OpenAI-compatible), ví dụ deploy tại [deep-seek-api-kappa.vercel.app](https://deep-seek-api-kappa.vercel.app/).

### 2. Chạy backend + frontend

**Terminal 1 — API Python (proxy giá vé + chat):**
```bash
pip install -r requirements.txt
python -m src.vinwonders.server
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm install
npm run dev
```

- **Chat trái**: **ReAct Agent** tra giá vé thật qua tools (`resolve_site` → `parse_visit_date` → `get_ticket_prices`), stream qua `POST /api/chat/stream`.
- **Tab Vé & Chuyến bay**: chọn khu vực / địa điểm / ngày → **Xem giá vé** (cùng crawler với agent).

### 3. Test agent (CLI)

```bash
python run_agent.py "T muốn đi Nha Trang cuối tuần sau, vé rẻ nhất bao nhiêu?"
python chatbot.py "cùng câu hỏi"   # baseline không có tool (để so sánh lab)
```

Cấu hình agent trong `.env`: `AGENT_PROVIDER=ds2api`, `DS2API_API_KEY`, `DS2API_MODEL`.

---

*Happy Coding! Let's build agents that actually work.*
