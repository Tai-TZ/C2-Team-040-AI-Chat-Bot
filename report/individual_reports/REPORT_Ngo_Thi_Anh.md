# Báo cáo Cá nhân: Lab 3 - Chatbot và ReAct Agent

* **Họ và tên:** Ngô Thị Ánh
* **Mã sinh viên:** 2A202600979
* **Ngày:** 01/06/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

### Các mô-đun đã triển khai

| Mô-đun                                            | Vai trò                                                                                                |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `api_server.py`                                   | Cung cấp các API FastAPI `/api/chat` và `/api/health`, kết nối backend Python với giao diện React      |
| `src/core/api_errors.py`                          | Ánh xạ các lỗi từ LLM/cấu hình/mạng thành mã HTTP và cấu trúc `{ code, message }`                      |
| `frontend/src/lib/api/chat.ts`                    | Client bao gồm `sendChatMessage`, `ChatApiError`, `formatChatApiError` và kiểm tra trạng thái hệ thống |
| `frontend/src/components/dashboard/ChatPanel.tsx` | Giao diện chat thời gian thực kết nối với API; hiển thị các bước suy luận và thông báo lỗi thân thiện  |
| `start.ps1`                                       | Khởi động môi trường phát triển bằng một lệnh (backend + frontend)                                     |

### Điểm nổi bật trong mã nguồn

#### 1. Xử lý lỗi HTTP có cấu trúc tại lớp API (`api_server.py`)

```python
except Exception as e:
    status, detail = exception_to_http(e)
    logger.log_event("API_ERROR", {"code": detail["code"], "status": status, ...})
    raise HTTPException(status_code=status, detail=detail) from e
```

#### 2. Ánh xạ ngoại lệ sang mã trạng thái HTTP (`src/core/api_errors.py`)

* `RateLimitError` hoặc lỗi vượt hạn mức → **429** `rate_limit`
* Thiếu API key (`ValueError`) → **503** `config_error`
* `APIConnectionError` → **502** `upstream_unreachable`
* Các lỗi khác → **500** `internal_error`

#### 3. Frontend phân tích lỗi API (`frontend/src/lib/api/chat.ts`)

```typescript
export class ChatApiError extends Error {
  readonly status: number;
  readonly code: string;
}
// parseErrorBody() đọc FastAPI detail: { code, message }
```

### Tài liệu: Tương tác với vòng lặp ReAct

Vòng lặp ReAct được triển khai trong `src/agent/agent.py` (do nhóm thực hiện). Công việc của tôi nằm **bên ngoài** vòng lặp nhưng cần thiết để trình diễn hệ thống thực tế:

1. Người dùng gửi tin nhắn từ `ChatPanel` → `POST /api/chat`.
2. `api_server` tạo một `ReActAgent` với `get_tool_definitions()` và gọi `agent.run(message)`.
3. Agent trả về `reply` cùng với `reasoning_steps` (được trích xuất từ các dòng `Thought:`).
4. Nếu LLM hoặc nhà cung cấp dịch vụ gặp lỗi, hàm `exception_to_http()` sẽ chuyển lỗi thành phản hồi HTTP phù hợp thay vì chỉ trả về lỗi 500 chung chung. Giao diện người dùng sẽ hiển thị thông báo dễ hiểu như hết hạn mức, thiếu API key hoặc backend ngoại tuyến.

Cách tách biệt này tuân theo thực tiễn phát triển phần mềm hiện đại: **logic của agent** được tách riêng khỏi **hợp đồng API và trải nghiệm người dùng (UX)**.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

### Mô tả Vấn đề

Khi kiểm thử giao diện chat VinWonders với DeepSeek/OpenAI, giao diện thường hiển thị lỗi chung hoặc JSON thô từ SDK (ví dụ: `429` hoặc `insufficient_quota`). Người dùng không thể xác định liệu cần chỉnh sửa file `.env`, chờ hết giới hạn truy cập hay khởi động lại backend.

Ngoài ra, trong quá trình chạy agent, mô hình đôi khi sinh ra lệnh:

```text
Action: check_stock(iPhone)
```

với chữ hoa không đúng định dạng, trong khi công cụ yêu cầu:

```text
iphone
```

Điều này dẫn đến lỗi miền dữ liệu và phát sinh thêm các bước ReAct không cần thiết.

### Nguồn Nhật ký (Log)

Hệ thống ghi log dưới dạng JSON trong thư mục:

```text
logs/YYYY-MM-DD.log
```

Ví dụ:

```json
{"event": "API_ERROR", "data": {"code": "rate_limit", "status": 429, "provider": "deepseek", "error": "..."}}
{"event": "AGENT_ERROR", "data": {"type": "PARSE_ERROR", "step": 2}}
{"event": "TOOL_CALL", "data": {"tool": "check_stock", "args": "iPhone", "observation": "Error: Product 'iPhone' not found..."}}
```

### Chẩn đoán

| Lỗi                                               | Nguyên nhân gốc                                                                                                                      |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Mọi lỗi API đều trả về HTTP 500                   | `api_server` bắt mọi ngoại lệ (`Exception`) và trả về `detail=str(e)` với mã 500, không phân biệt lỗi hạn mức, xác thực hay cấu hình |
| Giao diện nhận diện lỗi quota bằng tìm kiếm chuỗi | `ChatPanel` kiểm tra `message.includes("429")`, dễ hỏng khi định dạng thông báo backend thay đổi                                     |
| Sai khóa sản phẩm                                 | Prompt phiên bản 1 chưa nhấn mạnh yêu cầu viết thường; LLM sinh `iPhone` thay vì `iphone`                                            |

### Giải pháp

1. Thêm `src/core/api_errors.py` và tích hợp vào `api_server.py` để client nhận được phản hồi dạng:

```json
{
  "detail": {
    "code": "...",
    "message": "..."
  }
}
```

kèm mã trạng thái HTTP phù hợp.

2. Thay thế việc dò chuỗi bằng lớp `ChatApiError` và hàm `formatChatApiError()` trong `chat.ts`.

3. Nhóm sử dụng **prompt v2** với các quy tắc rõ ràng:

   * Tên sản phẩm phải viết thường.
   * Mã giảm giá viết hoa.
   * Chỉ gọi một công cụ trong mỗi bước.

Điều này giúp giảm lỗi tham số công cụ và số lần phân tích cú pháp thất bại.

### Kết quả

Người dùng sẽ thấy các thông báo như:

> API đã vượt quá giới hạn truy cập (rate limit/quota)...

thay vì một stack trace khó hiểu.

Trong khi đó, nhật ký của agent sẽ hiển thị các lỗi `PARSE_ERROR` hoặc lỗi từ công cụ dưới dạng **Observation**, cho phép mô hình tự phục hồi ở bước tiếp theo.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

### 1. Suy luận – `Thought` đã hỗ trợ như thế nào

Trong chế độ **chatbot** (`src/chatbot/chatbot.py`), mô hình trả lời trong một lần duy nhất.

Với câu hỏi:

> "Mua 2 chiếc iPhone với mã WINNER, giao đến Hà Nội — tổng tiền là bao nhiêu?"

chatbot thường **bịa ra giá** hoặc bỏ sót phí vận chuyển.

Ngược lại, trong chế độ **agent**, mỗi bước `Thought:` buộc mô hình lập kế hoạch rõ ràng:

> "Tôi cần kiểm tra tồn kho trước, sau đó áp dụng mã giảm giá, rồi tính phí vận chuyển."

Chuỗi `Action` → `Observation` giúp câu trả lời dựa trên dữ liệu thực tế từ công cụ. Danh sách `reasoning_steps` trên giao diện cũng giúp người dùng quan sát được quá trình suy luận, từ đó tăng khả năng gỡ lỗi và mức độ tin cậy.

### 2. Độ tin cậy – Khi nào Agent hoạt động kém hơn

* **Hỏi đáp đơn giản**

  Ví dụ:

  > "Các sản phẩm đang bán là gì?"

  Chatbot phản hồi nhanh hơn, ít tốn token hơn và không gặp rủi ro phân tích cú pháp. Trong khi đó, agent đôi khi vẫn thực hiện các lệnh `Action:` không cần thiết.

* **Độ trễ và chi phí**

  Mỗi bước ReAct tương ứng với một lần gọi LLM. Những truy vấn nhiều bước sẽ chậm và tốn chi phí hơn so với chatbot trả lời một lần.

* **Định dạng mong manh**

  Nếu mô hình xuất `Action` dưới dạng Markdown hoặc JSON, bộ phân tích cú pháp có thể thất bại. Đây là vấn đề mà chatbot không gặp phải.

### 3. Quan sát – Vai trò của phản hồi từ môi trường

Khi công cụ trả về:

```text
Error: Product 'iPhone' not found. Available: iphone, macbook, airpods
```

chuỗi này được thêm vào lịch sử dưới dạng:

```text
Observation:
```

Lượt gọi LLM tiếp theo thường sẽ tự sửa thành:

```text
check_stock(iphone)
```

Đây là điểm khác biệt cốt lõi so với chatbot:

> **Lỗi trở thành trạng thái để học hỏi và điều chỉnh, thay vì là nguyên nhân kết thúc cuộc hội thoại.**

Tuy nhiên, các lỗi ở tầng HTTP như `429` hoặc `503` không thể được xử lý bên trong vòng lặp agent. Chúng cần được giải quyết tại tầng API hoặc giao diện người dùng, đây cũng chính là phần đóng góp của tôi.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

### Khả năng mở rộng

* Thực thi các lời gọi công cụ bất đồng bộ khi công cụ truy cập API thực tế (quản lý kho, thanh toán,...).
* Truyền trực tiếp các token `Thought` lên giao diện thông qua SSE, trong khi vẫn giữ `Observation` đồng bộ.
* Sử dụng hàng đợi (Redis + Worker) cho các phiên agent kéo dài khi có nhiều người dùng đồng thời.

### An toàn

* Xác thực tham số công cụ bằng Pydantic trước khi thực thi để ngăn chặn tấn công chèn lệnh thông qua `args_str`.
* Bổ sung bước **giám sát (supervisor)** bằng một LLM thứ hai hoặc một bộ quy tắc để kiểm tra tính hợp lệ của `Action`.
* Giới hạn số bước (`max_steps`) và ngân sách token cho mỗi phiên làm việc (đã được triển khai một phần với `max_steps=6`).

### Hiệu năng

* Khi có hơn 20 công cụ, sử dụng **vector retrieval** để chỉ đưa các định nghĩa công cụ liên quan vào prompt thay vì liệt kê toàn bộ.
* Lưu bộ nhớ đệm (cache) cho các kết quả công cụ không thay đổi như `check_stock`.
* Áp dụng RAG cho tài liệu sản phẩm và chính sách của VinWonders, đồng thời duy trì các công cụ thương mại điện tử cho các phép tính có cấu trúc.

---

> **Ghi chú nộp bài:** Báo cáo được lưu dưới tên `REPORT_Ngo_Thi_Anh.md` theo yêu cầu của bài thực hành.
