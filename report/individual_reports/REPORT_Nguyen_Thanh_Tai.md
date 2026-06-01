# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Thành Tài
- **Student ID**: 2A202600627
- **Date**: 01/06/2026

---

## I. Technical Contribution (15 Points)

*Mô tả đóng góp cụ thể vào codebase — vai trò: frontend VinWonders dashboard, tích hợp full-stack (React ↔ FastAPI), LLM provider setup, dev tooling.*

- **Modules Implementated**:
  - **Project bootstrap** (`README.md`, `SCORING.md`, `EVALUATION.md`, `INSTRUCTOR_GUIDE.md`, `requirements.txt`, `.env.example`): khung Lab 3 và template báo cáo.
  - **Agent skeleton** (`src/agent/agent.py`): khung ReAct Thought–Action–Observation + telemetry `AGENT_START`/`AGENT_END`.
  - **LLM providers** (`src/core/openai_provider.py`, `gemini_provider.py`, `local_provider.py`, `provider_factory.py`): factory đa provider; cấu hình DeepSeek qua OpenAI-compatible API.
  - **Backend API** (`api_server.py`): FastAPI `/api/health`, `/api/chat`; CORS; mode `agent` | `chatbot`.
  - **CLI runner** (`main.py`): so sánh chatbot vs agent (giai đoạn ecommerce tools).
  - **Tools mẫu** (`src/tools/ecommerce_tools.py`, `tests/test_agent_offline.py`): 3 tool Lab ban đầu — sau team thay bằng VinWonders tools.
  - **Frontend dashboard** (`frontend/src/routes/index.tsx`, `Canvas.tsx`, `ChatPanel.tsx`, `ItineraryTimeline.tsx`, `LiveEvents.tsx`, `TicketsFlights.tsx`): UI split-view chat + canvas; mobile FAB.
  - **API client** (`frontend/src/lib/api/chat.ts`): `sendChatMessage`, `getApiHealth`, xử lý lỗi quota/API.
  - **Dev tooling** (`frontend/vite.config.ts`, `start.ps1`, `start.bat`, `package.json`): proxy `/api` → `:8000`; chạy backend + frontend một lệnh.
- **Code Highlights**:

Vite proxy tránh CORS khi dev; frontend gọi `/api/chat` cùng origin:

```15:24:frontend/vite.config.ts
  vite: {
    server: {
      proxy: {
        "/api": {
          target: "http://127.0.0.1:8000",
          changeOrigin: true,
        },
      },
    },
  },
```

Client TypeScript gửi message và nhận `reasoning_steps` từ agent:

```129:154:frontend/src/lib/api/chat.ts
export async function sendChatMessage(
  message: string,
  mode: ChatMode = "agent",
): Promise<ChatApiResponse> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, mode, provider: "deepseek" }),
    });
  } catch {
    throw new ChatApiError(
      "Không kết nối được backend. Chạy py api_server.py trên port 8000.",
      0,
      "network_error",
    );
  }

  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as ApiErrorBody;
    throw parseErrorBody(body, res.status, res.statusText);
  }

  return res.json() as Promise<ChatApiResponse>;
}
```

`reload_env()` — uvicorn `--reload` không tự cập nhật `.env` sau khi sửa key:

```10:20:src/core/provider_factory.py
def reload_env() -> None:
    """Reload .env on each request — uvicorn --reload does not refresh env vars."""
    load_dotenv(override=True)

def create_provider(
    provider_name: Optional[str] = None,
    model_name: Optional[str] = None,
) -> LLMProvider:
    reload_env()

    provider = (provider_name or os.getenv("DEFAULT_PROVIDER", "deepseek")).lower()
    model = model_name or os.getenv("DEFAULT_MODEL", "deepseek-v4-flash")
```

- **Documentation** (tương tác với vòng ReAct — góc nhìn full-stack):
  1. User gõ tin nhắn trong `ChatPanel` → `sendChatMessage()` POST `/api/chat`.
  2. `api_server.py` tạo `ReActAgent` hoặc `Chatbot` qua `create_provider()`.
  3. Agent chạy vòng Thought → Action → Observation; backend trả `reply` + `reasoning_steps[]`.
  4. UI render câu trả lời và accordion **Reasoning steps** — tiền đề cho tab Agent hoạt động (SSE) mà team mở rộng sau.
  5. `GET /api/health` kiểm tra backend online trước khi chat.

---

## II. Debugging Case Study (10 Points)

*Phân tích một sự cố thất bại cụ thể trong lab, dựa trên hệ thống logging.*

- **Problem Description**: Ban đầu `DEFAULT_PROVIDER=openai`. User gửi tin nhắn qua `ChatPanel` (vd. *"hi"*) → frontend hiện banner lỗi đỏ; chat hoàn toàn không phản hồi dù backend và UI đã chạy.
- **Log Source** (`logs/2026-06-01.log`):

```json
{"timestamp": "2026-06-01T07:16:39.965516", "event": "AGENT_START", "data": {"input": "hi", "model": "gpt-4o", "prompt_version": "v2"}}
{"timestamp": "2026-06-01T07:16:43.988875", "event": "API_ERROR", "data": {"error": "Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details...', 'type': 'insufficient_quota', 'code': 'insufficient_quota'}}", "message": "hi"}}
```

Sau khi chuyển DeepSeek, log xác nhận provider mới hoạt động:

```json
{"timestamp": "2026-06-01T07:40:16.542960", "event": "API_CHAT", "data": {"provider": "deepseek", "model": "deepseek-v4-flash", "mode": "chatbot"}}
{"timestamp": "2026-06-01T07:40:45.184274", "event": "API_CHAT", "data": {"provider": "deepseek", "model": "deepseek-v4-flash", "mode": "agent"}}
```

- **Diagnosis**:
  - **Provider / billing**: OpenAI key hết quota (`429 insufficient_quota`) — không phải lỗi ReAct loop hay frontend.
  - **Cấu hình**: `load_dotenv()` chỉ đọc `.env` một lần lúc import; sửa provider trong `.env` không có hiệu lực ngay khi uvicorn `--reload`.
  - **UI**: Lỗi thô từ API khó hiểu với user demo — cần map sang message tiếng Việt.
- **Solution** (commit `0f8fc79`, `6ec9081`):
  1. Đổi default sang **DeepSeek** trong `provider_factory.py` và `.env.example`.
  2. Thêm `reload_env()` trước mỗi request; `/api/health` trả `{ provider, model }` để xác nhận cấu hình.
  3. `ChatPanel` + `formatChatApiError()` map lỗi 429/quota → hướng dẫn đổi provider hoặc kiểm tra key.
  4. Validate sớm: `ValueError("DEEPSEEK_API_KEY chưa được cấu hình trong .env")` thay vì fail mơ hồ.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Suy ngẫn về khác biệt khả năng suy luận giữa chatbot và agent.*

1. **Reasoning**: Với **chatbot**, `ChatPanel` chỉ nhận một chuỗi `reply` — không biết model suy nghĩ gì. Với **agent**, field `reasoning_steps[]` cho phép UI hiển thị từng bước Thought/Action/Observation; khi demo, mở accordion reasoning giúp chứng minh agent có quy trình, không chỉ “đoán” câu trả lời.
2. **Reliability**: Agent **kém hơn** chatbot khi: (a) câu chào/FAQ đơn giản — agent chậm hơn vì nhiều round-trip LLM; (b) backend hoặc API key lỗi — agent trả `reasoning_steps` rỗng, UX tệ hơn chatbot; (c) chưa có structured UI — user chỉ thấy loading lâu mà không rõ agent đang làm gì. Agent chỉ “thắng” khi hiển thị được giá trị thêm (trace, giá/thời tiết thật từ tool).
3. **Observation**: Ban đầu Observation chỉ xuất hiện trong `reasoning_steps` dạng text. Đây là feedback môi trường từ tool (giá, stock, lỗi API) buộc bước LLM tiếp theo dựa trên dữ liệu thật — khác chatbot one-shot. Contract API tôi định nghĩa ở `api_server.py` + `chat.ts` là nền để team sau này đẩy Observation JSON sang Canvas qua SSE `structured`.

---

## IV. Future Improvements (5 Points)

*Cách mở rộng hệ thống agent lên mức production.*

- **Scalability**: Tách `api_server.py` thành service Docker riêng; deploy frontend static (Vercel/Cloudflare) với API gateway thay Vite dev proxy; thống nhất một entrypoint SSE thay hai server song song.
- **Safety**: Rate limit `/api/chat` theo IP/session; supervisor rule-based audit `Action` trước khi execute tool; giới hạn chi phí theo session qua telemetry.
- **Performance**: Streaming token end-to-end (optimistic UI); cache response `/api/health`; prefetch provider/model badge trên header chat; worker queue cho tool gọi API nặng để không block SSE.

