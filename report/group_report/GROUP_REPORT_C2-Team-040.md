# Group Report: Lab 3 — VinWonders ReAct Agent (C2-Team-040)

- **Team Name**: Nhóm 10
- **Product**: VinWonders Tour Guide
- **Deployment**: `python -m src.vinwonders.server` + `cd frontend && npm run dev`
- **Date**: 2026-06-01

---

## 1. Executive Summary

Chúng tôi xây dựng **chatbot baseline** (một lần gọi LLM, không tool) và **ReAct agent** với 5 tool VinWonders thật (địa điểm, ngày, thời tiết OpenWeatherMap, giá vé API). **Agent v2** thêm bootstrap pipeline, guardrails chống Final Answer sớm, và UI trace/streaming.

- **Offline eval**: 6/6 checks pass — `python scripts/eval_lab3.py --offline`
- **Key outcome**: Với câu hỏi đa bước (*"Nha Trang cuối tuần sau, check thời tiết và giá vé"*), chatbot có thể **bịa giá**; agent của chúng tôi trả lời dựa trên **Observation** từ API và hiển thị map + giá được lấy *TRỰC TIẾP* từ VinWonders.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop

Xem sơ đồ: `[docs/LAB3_ARCHITECTURE.md](../../docs/LAB3_ARCHITECTURE.md)`

```
Thought → Action → Observation → … → Final Answer
```

SSE events: `trace`, `agent_step`, `structured`, `dashboard`, `content`.

### 2.2 Tool Inventory (5 tools — >2 required)


| Tool                   | Input                         | Output / Use case                  |
| ---------------------- | ----------------------------- | ---------------------------------- |
| `list_destinations`    | `region_query?`               | JSON danh sách site + supplierCode |
| `resolve_site`         | `query`                       | region, supplierCode, attractions  |
| `parse_visit_date`     | `expression`                  | `usingDate` DD-MM-YYYY             |
| `get_weather_forecast` | `location`, `using_date`      | temp, rain risk, recommendation    |
| `get_ticket_prices`    | `supplier_code`, `using_date` | Live tickets + cheapestFormatted   |


### 2.3 Agent versions


| Version      | Mô tả                                          | File chính                          |
| ------------ | ---------------------------------------------- | ----------------------------------- |
| **Chatbot**  | Không tool, prompt tĩnh                        | `src/chatbot/vinwonders_chatbot.py` |
| **Agent v1** | ReAct + prompt tối giản, không bootstrap/guard | `prompt_version="v1"`               |
| **Agent v2** | Karphany + bootstrap + guardrails + streaming  | `prompt_version="v2"`               |


### 2.4 LLM Providers

- **Primary**: OpenRouter (`AGENT_PROVIDER=openrouter`) — DeepSeek Chat
- **Fallback**: DS2API gateway, OpenAI, Gemini (via `src/core/factory.py`)

---

## 3. Telemetry & Performance Dashboard

Mỗi lần gọi LLM ghi `LLM_METRIC` vào `logs/YYYY-MM-DD.log`:

- `prompt_tokens`, `completion_tokens`, `completion_to_prompt_ratio`
- `latency_ms`, `cost_estimate_usd` (bảng giá theo model trong `src/telemetry/metrics.py`)

**API**: `GET /api/telemetry/session` → `session_summary()` (P50/P99 latency, tổng token, tổng cost).

Chạy compare có telemetry:

```bash
python main.py compare
```

---

## 4. Root Cause Analysis — Failure Traces

Chi tiết JSON: `[report/traces/](../traces/)`

### Case: Premature Final Answer (v1)

- **Input**: "Nha Trang cuối tuần sau giá vé bao nhiêu?"
- **Observation**: Model trả `Final Answer` với giá VND **không** có trong tool output.
- **Root cause**: Không ép thứ tự tool; không bootstrap.
- **Fix (v2)**: `guardrails.reject_premature_final()` + `run_bootstrap_pipeline()` — xem `TRACE_FAILURE_PREMATURE_FINAL.json`.

### Case: Invalid tool arguments

- **Observation**: `resolve_site(location="Nha Trang")` → lỗi tham số.
- **Fix**: `registry._sanitize_tool_args()` map `location` → `query`.

---

## 5. Ablation & Evaluation

### Experiment: Chatbot vs Agent v1 vs Agent v2

```bash
python main.py compare
# hoặc
python scripts/eval_lab3.py --live   # cần API key
```


| Case                      | Chatbot                | Agent v2                 | Winner             |
| ------------------------- | ---------------------- | ------------------------ | ------------------ |
| Giá + thời tiết Nha Trang | Thường ước lượng / bịa | Tool API + guardrails    | **Agent**          |
| "Có gì chơi?"             | Mô tả chung            | resolve_site + map embed | **Agent**          |
| Off-topic (code Python)   | Có thể trả lời         | Từ chối Karphany         | **Agent** (policy) |


Kết quả offline: `report/eval/offline_results.json`.

### Prompt v1 vs v2

- **v1**: Prompt ngắn, không Karphany, không pipeline bắt buộc.
- **v2**: Prompt đầy đủ + guardrails → giảm lỗi Final Answer sớm và off-topic.

---

## 6. Production Readiness

- **Security**: Tool args sanitized; không commit `.env`.
- **Guardrails**: `max_steps=10`; reject premature final; off-topic hints.
- **Scaling**: Trace module tách (`src/agent/trace.py`); có thể chuyển LangGraph cho nhánh phức tạp.

---

## 7. Code Quality & Modularity


| Module                                | Responsibility           |
| ------------------------------------- | ------------------------ |
| `src/utils/text.py`, `money.py`       | Shared helpers           |
| `src/vinwonders/destinations_data.py` | Single JSON loader       |
| `src/agent/trace.py`                  | Parse agent trace        |
| `src/agent/guardrails.py`             | v2 failure handling      |
| `src/agent/bootstrap.py`              | Auto pipeline            |
| `src/tools/registry.py`               | Tool registry + sanitize |


Tests: `tests/test_vinwonders_scoring.py` (7 tests, no API).

---

## 8. Bonus Points Claimed


| Bonus                     | Evidence                                                            |
| ------------------------- | ------------------------------------------------------------------- |
| **Extra Monitoring (+3)** | `cost_estimate_usd`, token ratio, P50/P99, `/api/telemetry/session` |
| **Extra Tools (+2)**      | 5 tools + map embed + live weather/prices                           |
| **Failure Handling (+3)** | `guardrails.py`, bootstrap, arg sanitize                            |
| **Live Demo (+5)**        | VinWonders web UI + `python -m src.vinwonders.server`               |
| **Ablation (+2)**         | v1 vs v2, chatbot compare in `main.py`                              |


---

## Appendix — Commands

```bash
python chatbot.py "Nha Trang giá vé?"
python run_agent.py "Nha Trang cuối tuần sau" --version v2
python main.py eval --offline
python -m pytest tests/test_vinwonders_scoring.py -q
```

Tool evolution: `[report/TOOL_DESIGN_EVOLUTION.md](../TOOL_DESIGN_EVOLUTION.md)`