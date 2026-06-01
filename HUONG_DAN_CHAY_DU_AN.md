# Hướng dẫn chạy dự án — VinWonders Tour Guide

Tài liệu này hướng dẫn cài đặt và chạy **web app VinWonders** (chat AI + giá vé) và các lệnh CLI Lab 3 trên Windows.

---

## 1. Yêu cầu hệ thống


| Thành phần  | Phiên bản gợi ý        |
| ----------- | ---------------------- |
| **Python**  | 3.12+ (`py --version`) |
| **Node.js** | 18+ (`node --version`) |
| **npm**     | 9+                     |
| **Git**     | Tùy chọn (clone repo)  |


**API key cần có** (tối thiểu để chat + thời tiết hoạt động đầy đủ):

- `OPENROUTER_API_KEY` — khuyến nghị cho agent web (hoặc `DS2API_API_KEY`)
- `OPENWEATHER_API_KEY` — tool kiểm tra thời tiết trước khi tư vấn vé

---

## 2. Cài đặt lần đầu

Mở terminal tại thư mục gốc dự án:

```powershell
cd "C:\Users\...\C2-Team-040-AI-Chat-Bot"
```

### Bước 1 — Virtualenv Python

```powershell
py -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

> Dùng `.venv` (không commit thư mục `env/` lên Git).

### Bước 2 — Cấu hình biến môi trường

```powershell
copy .env.example .env
```

Mở `.env` và điền key thật:

```env
# Agent web (khuyến nghị)
AGENT_PROVIDER=openrouter
AGENT_MODEL=deepseek/deepseek-chat
OPENROUTER_API_KEY=sk-or-v1-...

# Thời tiết (bắt buộc cho tool get_weather_forecast)
OPENWEATHER_API_KEY=...

# Dự phòng — DS2API / DeepSeek gateway
DS2API_API_KEY=...
DS2API_BASE_URL=https://deep-seek-api-kappa.vercel.app
```

### Bước 3 — Frontend

```powershell
cd frontend
npm install
cd ..
```

---

## 3. Chạy web app (khuyến nghị — demo Lab 3)

Cần **2 terminal** (backend `:8000` + frontend `:8080`).

### Terminal 1 — Backend VinWonders

```powershell
.\.venv\Scripts\python -m src.vinwonders.server
```

Khi thành công, thấy Uvicorn chạy tại `http://127.0.0.1:8000`.

Kiểm tra nhanh:

```powershell
curl http://127.0.0.1:8000/api/destinations
```

### Terminal 2 — Frontend

```powershell
cd frontend
npm run dev
```

Mở trình duyệt: **[http://localhost:8080](http://localhost:8080)**


| Khu vực UI              | Chức năng                                    |
| ----------------------- | -------------------------------------------- |
| **Chat trái**           | Hỏi AI Karphany — agent ReAct stream qua SSE |
| **Canvas phải**         | Dashboard, giá vé, map                       |
| **Tab Agent hoạt động** | Trace Thought / Action / Observation         |


**Câu hỏi demo gợi ý:**

```
Nha Trang cuối tuần sau, check thời tiết và giá vé bao nhiêu?
Nha Trang có gì chơi?
```

Frontend dev proxy `/api` → backend `:8000` (cấu hình trong `frontend/vite.config.ts`).

---

## 4. Chạy một lệnh (Windows)

### Cách A — Script PowerShell

```powershell
.\start.ps1
```

- Nếu đã cài `concurrently` ở root: chạy `npm run dev` (backend + frontend một terminal).
- Nếu chưa: mở **2 cửa sổ** — backend `api_server.py` + frontend.

> `start.ps1` dùng `**api_server.py`** (stack legacy). Demo VinWonders đầy đủ SSE nên dùng **§3** (`src.vinwonders.server`).

### Cách B — npm concurrently (root)

```powershell
npm install
npm run dev
```

Chạy `api_server.py` + `frontend` — cần `.venv` và `frontend/node_modules` đã cài.

---

## 5. Lệnh CLI (không cần mở web)

Kích hoạt venv trước mỗi lệnh:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Chatbot baseline (không tool)

```powershell
python chatbot.py "Nha Trang cuối tuần sau giá bao nhiêu?"
```

### ReAct agent

```powershell
python run_agent.py "Nha Trang cuối tuần sau" --version v2
python run_agent.py "Nha Trang cuối tuần sau" --version v1
```

### So sánh chatbot vs agent

```powershell
python main.py compare
```

### Đánh giá offline (6/6, không cần API)

```powershell
python scripts/eval_lab3.py --offline
python main.py eval --offline
python -m pytest tests/test_vinwonders_scoring.py -q
```

---

## 6. Cổng & URL tham chiếu


| Dịch vụ         | URL                                                 |
| --------------- | --------------------------------------------------- |
| Frontend        | [http://localhost:8080](http://localhost:8080)      |
| Backend API     | [http://127.0.0.1:8000](http://127.0.0.1:8000)      |
| Chat SSE        | `POST /api/chat/stream`                             |
| Giá vé          | `GET /api/prices?supplier_code=...&date=DD-MM-YYYY` |
| Telemetry       | `GET /api/telemetry/session`                        |
| Health (legacy) | `GET /api/health`                                   |


---

## 7. Xử lý lỗi thường gặp

### Frontend: "Không kết nối được backend"

1. Kiểm tra backend đang chạy: `python -m src.vinwonders.server`
2. Port 8000 không bị chiếm bởi process khác
3. Frontend chạy qua `npm run dev` (có proxy `/api`)

### Chat báo lỗi API key / 401 / 429

1. Mở `.env` — kiểm tra `OPENROUTER_API_KEY` hoặc `DS2API_API_KEY`
2. `AGENT_PROVIDER=openrouter` khớp với key đã điền
3. **Restart backend** sau khi sửa `.env`

### Thời tiết không có / tool lỗi

- Bổ sung `OPENWEATHER_API_KEY` trong `.env`
- Restart backend

### Giá vé trống hoặc lỗi crawler

- Kiểm tra mạng; API VinWonders có thể rate-limit
- Thử ngày định dạng `DD-MM-YYYY` hoặc câu có "cuối tuần sau"

### `python` không nhận lệnh (Windows)

Dùng `py` thay `python`:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m src.vinwonders.server
```

### Log debug

- File log: `logs/YYYY-MM-DD.log` (JSON từng dòng)
- Events: `AGENT_START`, `TOOL_CALL`, `LLM_METRIC`, `API_ERROR`

---

## 8. Tài liệu liên quan


| File                                             | Nội dung                        |
| ------------------------------------------------ | ------------------------------- |
| [TECHNICAL_DOCUMENT.md](./TECHNICAL_DOCUMENT.md) | Tech stack, kiến trúc, workflow |
| [LAB3_ARCHITECTURE.md](./LAB3_ARCHITECTURE.md)   | Sơ đồ hệ thống                  |
| [README.md](../README.md)                        | Tổng quan Lab 3                 |
| [SCORING.md](../SCORING.md)                      | Tiêu chí chấm điểm              |


---

