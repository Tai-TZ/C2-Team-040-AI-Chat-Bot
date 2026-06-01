# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: Nhóm 10
- **Team Members**:
  - Nguyễn Trọng Nguyên — 2A202600548
  - Nguyễn Thành Tài — 2A202600627
  - Ngô Thị Ánh — 2A202600979
- **Deployment Date**: 2026-06-01

---

## 1. Executive Summary

*Tổng quan mục tiêu agent VinWonders Tour Guide (chatbot baseline vs ReAct agent v2) và tỷ lệ thành công so với chatbot.*

- **Success Rate**: **100%** (6/6 checks offline) — `python scripts/eval_lab3.py --offline`; live demo web UI + agent v2 trên câu hỏi đa bước VinWonders.
- **Key Outcome**: Với câu hỏi *"Nha Trang cuối tuần sau, check thời tiết và giá vé"*, chatbot baseline có thể **bịa giá VND**; agent v2 trả lời dựa trên **Observation** từ OpenWeatherMap + API giá vé VinWonders, kèm map embed và structured cards trên UI.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

*Mô tả vòng Thought → Action → Observation → Final Answer; sơ đồ chi tiết: [docs/LAB3_ARCHITECTURE.md](../../docs/LAB3_ARCHITECTURE.md).*

```
Thought → Action → Observation → … → Final Answer
```

- **SSE events** (web demo): `trace`, `agent_step`, `structured`, `dashboard`, `content`.
- **Agent v1**: ReAct + prompt tối giản, không bootstrap/guardrails.
- **Agent v2**: Persona Karphany + `run_bootstrap_pipeline()` + `guardrails.reject_premature_final()` + streaming (`prompt_version="v2"`).
- **Chatbot baseline**: Một lần gọi LLM, không tool — `src/chatbot/vinwonders_chatbot.py`.

### 2.2 Tool Definitions (Inventory)

| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `list_destinations` | `region_query?` (string) | Liệt kê site VinWonders + `supplierCode`. |
| `resolve_site` | `query` (string) | Xác định region, mã NTVW, danh sách attraction. |
| `parse_visit_date` | `expression` (string) | Chuyển "cuối tuần sau" → `usingDate` DD-MM-YYYY. |
| `get_weather_forecast` | `location`, `using_date` | Nhiệt độ, mưa, gợi ý từ OpenWeatherMap. |
| `get_ticket_prices` | `supplier_code`, `using_date` | Giá vé live + `cheapestFormatted`. |

### 2.3 LLM Providers Used

- **Primary**: OpenRouter (`AGENT_PROVIDER=openrouter`) — DeepSeek Chat
- **Secondary (Backup)**: DS2API gateway; OpenAI; Gemini (via `src/core/factory.py`)

---

## 3. Telemetry & Performance Dashboard

*Phân tích metric thu thập trong phiên test ngày 2026-06-01 (`logs/2026-06-01.log`, 14 lần gọi `LLM_METRIC`). API live: `GET /api/telemetry/session`.*

- **Average Latency (P50)**: **9534 ms**
- **Max Latency (P99)**: **17662 ms**
- **Average Tokens per Task**: **808 tokens** (trung bình `total_tokens` mỗi lần gọi LLM)
- **Total Cost of Test Suite**: **$0.11** (tổng `cost_estimate` / `cost_estimate_usd` trong log phiên demo)

---

## 4. Root Cause Analysis (RCA) - Failure Traces

*Phân tích sâu nguyên nhân agent thất bại trong giai đoạn v1.*

### Case Study: Premature Final Answer (Agent v1)

- **Input**: "Nha Trang cuối tuần sau giá vé bao nhiêu?"
- **Observation**: Model trả `Final Answer` với mức giá VND **không xuất hiện** trong output của `get_ticket_prices` / `get_weather_forecast`; trace kết thúc `max_steps` hoặc hallucination giá (xem `report/traces/TRACE_FAILURE_PREMATURE_FINAL.json`).
- **Root Cause**: Prompt v1 không ép thứ tự tool (weather → prices); không có bootstrap pipeline; guardrails chưa từ chối Final Answer khi thiếu Observation bắt buộc.

**Khắc phục (v2)**: `guardrails.reject_premature_final()` + `run_bootstrap_pipeline()` + `registry._sanitize_tool_args()` (map `location` → `query` khi model gọi sai tên tham số).

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2

- **Diff**: v2 thêm persona Karphany, pipeline bootstrap bắt buộc (`resolve_site` → `parse_visit_date` → `get_weather_forecast` → `get_ticket_prices`), guardrails chống Final Answer sớm và off-topic.
- **Result**: Offline check `guardrail_premature_final` và `bootstrap_pipeline_tools` **pass**; RCA case §4 không tái diễn trên v2 trong eval offline (6/6).

### Experiment 2 (Bonus): Chatbot vs Agent

```bash
python main.py compare
python scripts/eval_lab3.py --live   # cần API key
```

| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Chào / FAQ đơn giản | Trả lời nhanh, đủ dùng | Chậm hơn (nhiều bước LLM) | Draw |
| Giá + thời tiết Nha Trang | Thường ước lượng / bịa VND | Tool API + guardrails + map/giá thật | **Agent** |
| Off-topic (code Python) | Có thể trả lời lan man | Từ chối theo policy Karphany | **Agent** |

Kết quả offline chi tiết: `report/eval/offline_results.json`.

---

## 6. Production Readiness Review

*Cân nhắc đưa hệ thống VinWonders agent lên môi trường thật.*

- **Security**: `_sanitize_tool_args()` trước khi execute tool; không commit `.env`; CORS giới hạn origin dev/demo.
- **Guardrails**: `max_steps=10`; từ chối Final Answer sớm; gợi ý off-topic; fallback answer từ trace khi LLM lỗi sau khi tool đã chạy.
- **Scaling**: Module tách (`src/agent/trace.py`, `guardrails.py`, `bootstrap.py`); telemetry P50/P99 qua `session_summary()`; có thể chuyển LangGraph cho nhánh multi-destination / indoor khi mưa.
