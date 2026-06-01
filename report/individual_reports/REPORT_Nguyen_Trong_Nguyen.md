# Individual Report: Lab 3 — Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Trọng Nguyên
- **Student ID**: 2A202600548
- **Branch / vai trò**: Backend agent, tools, VinWonders API, OpenWeatherMap API, tích hợp frontend
- **Date**: 01/06/2026

---

## I. Technical Contribution (15 Points)

Phần lớn công việc tập trung biến demo VinWonders thành hệ thống đủ tiêu chí Lab 3 (chatbot baseline → ReAct v1 → ReAct v2 + monitoring + báo cáo).

### Modules đã triển khai / chỉnh sửa chính


| Lớp                    | File / module                                                                                                            | Đóng góp                                                                                      |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| **Crawler & API**      | `src/vinwonders/crawler.py`, `server.py`                                                                                 | Proxy giá vé thật từ booking API; SSE chat `/api/chat/stream`; CORS; xử lý lỗi HTTP           |
| **Tools (5)**          | `src/tools/destinations.py`, `dates.py`, `weather.py`, `prices.py`, `registry.py`                                        | Tool spec VinWonders; `_sanitize_tool_args` map lỗi tham số LLM                               |
| **ReAct Agent**        | `src/agent/agent.py`                                                                                                     | Vòng Thought–Action–Observation; bootstrap; guardrails; stream Final Answer; SSE `agent_step` |
| **Agent v2**           | `src/agent/bootstrap.py`, `guardrails.py`, `structured.py`, `trace.py`                                                   | Pipeline tự động; chặn Final Answer sớm; payload UI (giá, thời tiết, map)                     |
| **Prompt**             | `src/prompts/vinwonders.py`                                                                                              | Persona Karphany; prompt v1/v2; từ chối off-topic                                             |
| **Chatbot baseline**   | `src/chatbot/vinwonders_chatbot.py`, `chatbot.py`                                                                        | Một lần gọi LLM, không tool — đối chiếu với agent                                             |
| **Dữ liệu**            | `vinwonders_destinations_data.json`, `destinations_data.py`, `destination_maps.py`                                       | Điểm đến + tọa độ map embed nội bộ                                                            |
| **Telemetry**          | `src/telemetry/metrics.py`, `logger.py`                                                                                  | `LLM_METRIC`: token, latency, `cost_estimate_usd`, ratio; `GET /api/telemetry/session`        |
| **Frontend**           | `ChatPanel.tsx`, `AILoadingState.tsx`, `AgentActivityPanel.tsx`, `VinWondersMapEmbed.tsx`, `chat-api.ts`                 | Loading state, trace agent, map trong câu trả lời, streaming                                  |
| **Lab 3 deliverables** | `main.py`, `scripts/eval_lab3.py`, `tests/test_vinwonders_scoring.py`, `report/group_report/GROUP_REPORT_C2-Team-040.md` | So sánh chatbot/agent; eval offline; group report                                             |


### Commit tiêu biểu trên `nguyenBranch`

- `ecd822a` — VinWonders price crawler, DS2API chat, dashboard
- `ec4eef5` — ReAct agent + structured UI + price cards
- `334af5d` — Xử lý lỗi HTTP API
- `9de2fbf` — Weather, dashboard sync, AI loading UI
- `30daf57` — AI loading / trace SSE
- Merge `main` + cải tiến SCORING (guardrails, eval, map, OpenRouter)

### Code highlight — sanitize tool args (giảm lỗi v1)

Model thường gọi `resolve_site(location="Nha Trang")` thay vì `query`. Registry chuẩn hóa trước khi gọi handler:

```78:88:src/tools/registry.py
def _sanitize_tool_args(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    raw = {k: v for k, v in (args or {}).items() if not _is_placeholder(v)}

    if tool_name == "resolve_site":
        q = raw.get("query") or raw.get("location") or raw.get("region") or raw.get("siteName")
        return {"query": str(q).strip()} if q else {}
```

### Tương tác với vòng ReAct

1. User gửi câu hỏi → `ReActAgent.run_with_events()`.
2. **Bootstrap (v2)** chạy `resolve_site` → `parse_visit_date` → `get_weather_forecast` → `get_ticket_prices` nếu nhận diện intent du lịch.
3. Mỗi bước model: `Thought` → `Action` → `execute_tool` → `Observation` ghi vào `trace` + log `TOOL_CALL` / `TOOL_RESULT`.
4. **Guardrails (v2)** từ chối `Final Answer` nếu thiếu weather/prices.
5. `finalize_structured_payload(trace)` → SSE `structured` (thẻ giá, thời tiết, `destinationMap`) → frontend render.

---

## II. Debugging Case Study (10 Points)

### Case A — Agent gọi tool sai tham số, hết `max_steps` (Agent v1)

**Mô tả:** User hỏi *"Nha Trang cuối tuần sau, check thời tiết và giá vé"*. Model gọi `parse_visit_date(location="cuối tuần sau")` hoặc nhảy `Final Answer` khi mới có `resolve_site` → 8–10 vòng lặp vô ích, UI trống, không có structured cards.

**Log:** Không có `TOOL_RESULT` hợp lệ cho `get_weather_forecast` / `get_ticket_prices`; event `AGENT_END` với `"status": "max_steps"` (xem thêm `report/traces/TRACE_FAILURE_PREMATURE_FINAL.json`).

**Chẩn đoán:**

- **Prompt:** v1 không ép thứ tự tool rõ như v2.
- **Tool spec:** Tên tham số strict (`expression` vs `location`).
- **Model:** DeepSeek đôi khi “đoán” giá thay vì gọi API.

**Giải pháp (Agent v2 — đã merge trên `main` / `nguyenBranch`):**

1. `registry._sanitize_tool_args` — map alias tham số.
2. `bootstrap.py` — chạy pipeline đúng thứ tự trước vòng LLM.
3. `guardrails.reject_premature_final()` — inject Observation *"CHƯA ĐƯỢC PHÉP Final Answer..."*.
4. `structured.py` + SSE — UI vẫn có dữ liệu từ trace dù LLM chậm.

---

### Case B — DS2API HTTP 500 (`upload file failed`)

**Mô tả:** Stream chat trả lỗi 500 từ gateway DS2API khi context dài hoặc proxy lỗi.

**Log / triệu chứng:** Frontend `formatChatApiError`; không có `AGENT_END` thành công; user thấy banner lỗi đỏ.

**Chẩn đoán:** Phụ thuộc proxy bên thứ ba, không phải logic ReAct.

**Giải pháp:**

- Chuyển `AGENT_PROVIDER=openrouter` trong `.env` (`src/core/factory.py`).
- Rút gọn Observation đưa vào prompt (`_observation_for_prompt` trong `agent.py`) để giảm token.
- `build_fallback_answer()` — vẫn trả summary từ trace khi LLM fail sau khi tool đã chạy.

---

### Case C — Thiếu `OPENWEATHER_API_KEY`

**Log thật** (`logs/2026-06-01.log`):

```json
{"event": "TOOL_RESULT", "data": {"tool": "get_weather_forecast", "preview": "{\"error\": \"OPENWEATHER_API_KEY is not set in .env\"}"}}
```

**Giải pháp:** Bổ sung key trong `.env`; sau đó Observation có `hasRain`, `recommendation` — agent tư vấn dời ngày / hoạt động trong nhà (đúng rubric “weather before tickets”).

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning — vai trò khối `Thought`

Với **chatbot** (`VinWondersChatbot`), model trả lời trực tiếp từ weights + danh sách điểm đến tĩnh trong prompt — không có bước “suy nghĩ” tách bạch và không có số liệu live.

Với **agent**, `Thought` buộc model **lập kế hoạch** trước mỗi `Action` (vd: *"Đã có NTVW1, cần parse ngày trước khi tra giá"*). Điều này giúp debug: đọc trace là biết model **định** làm gì, không chỉ kết quả cuối.

### 2. Reliability — khi Agent **kém hơn** Chatbot


| Tình huống                       | Chatbot                                                         | Agent                             |
| -------------------------------- | --------------------------------------------------------------- | --------------------------------- |
| Câu chào / FAQ chung             | Nhanh, đủ dùng                                                  | Chậm hơn (nhiều round-trip)       |
| Mạng/API lỗi                     | Vẫn có thể trả lời chung chung                                  | Dễ fail hoặc message kỹ thuật     |
| Câu off-topic                    | Đôi khi vẫn trả lời lan man                                     | v2 từ chối có chủ đích (Karphany) |
| Câu cần **giá + thời tiết thật** | Hay **bịa** VND (log bước 4 cũ từng Final Answer trước đủ tool) | Đúng hơn nếu pipeline chạy đủ     |


Kết luận cá nhân: Agent chỉ “thắng” khi có **tool ổn định + guardrails**; không thì chatbot đôi khi **nghe có vẻ hợp lý hơn** nhưng sai sự thật.

### 3. Observation — feedback môi trường

Observation JSON (giá vé, `cheapestFormatted`, `hasRain`) là **nguồn sự thật** cho bước sau. Ví dụ sau `get_weather_forecast` với `hasRain: true`, bước tiếp theo model (hoặc structured UI) gợi ý dời ngày — đúng hành vi **environment feedback** của ReAct, khác hẳn chatbot một shot.

Frontend quan sát được qua tab **Agent hoạt động** (`agent_step` SSE) — hỗ trợ demo BGK và RCA trong báo cáo nhóm.

---

## IV. Future Improvements (5 Points)

### Scalability

- Tách tool gọi API sang **worker queue** (Celery / Redis) để không block SSE; agent chờ `job_id` trong Observation.
- Cache giá vé theo `(supplier_code, using_date)` TTL 15–30 phút giảm tải crawler.

### Safety

- **Supervisor** nhỏ (rule hoặc LLM) audit `Action` trước khi execute (chặn tool không trong whitelist).
- Giới hạn chi phí theo session qua `tracker.session_summary()` — dừng khi vượt ngưỡng token/cost.

### Performance & sản phẩm

- **RAG** trên tài liệu chính sách VinWonders + FAQ show (vector DB) cho câu hỏi mơ hồ.
- **LangGraph** cho nhánh: đã có giá → gợi ý combo; mưa → nhánh indoor; multi-destination trip.
- Map: nhiều marker trên một iframe hoặc Mapbox thay OSM embed đơn giản.

