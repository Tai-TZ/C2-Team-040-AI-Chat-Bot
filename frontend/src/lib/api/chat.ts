export type ChatMode = "agent" | "chatbot";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  reasoningSteps?: string[];
}

export interface ChatApiResponse {
  reply: string;
  reasoning_steps: string[];
  mode: ChatMode;
  provider?: string;
}

export interface ApiHealth {
  ok: boolean;
  provider?: string;
  model?: string;
}

/** Structured error from FastAPI: { detail: { code, message } } or validation array */
export interface ApiErrorBody {
  detail?:
    | string
    | { code?: string; message?: string }
    | Array<{ msg?: string; loc?: unknown[] }>;
}

export class ChatApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(message: string, status: number, code = "unknown") {
    super(message);
    this.name = "ChatApiError";
    this.status = status;
    this.code = code;
  }
}

const API_BASE = import.meta.env.VITE_API_URL ?? "";

function parseErrorBody(body: ApiErrorBody, status: number, statusText: string): ChatApiError {
  const detail = body.detail;

  if (typeof detail === "string" && detail.trim()) {
    return new ChatApiError(detail, status, httpCodeToErrorCode(status));
  }

  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    const message =
      typeof detail.message === "string" && detail.message.trim()
        ? detail.message
        : statusText || "Yêu cầu thất bại";
    const code =
      typeof detail.code === "string" && detail.code.trim()
        ? detail.code
        : httpCodeToErrorCode(status);
    return new ChatApiError(message, status, code);
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const message = detail.map((d) => d.msg ?? "Invalid input").join("; ");
    return new ChatApiError(message, status, "validation_error");
  }

  return new ChatApiError(
    statusText || "Không thể kết nối tới AI server",
    status,
    httpCodeToErrorCode(status),
  );
}

function httpCodeToErrorCode(status: number): string {
  const map: Record<number, string> = {
    400: "bad_request",
    401: "auth_error",
    403: "permission_denied",
    404: "not_found",
    429: "rate_limit",
    502: "upstream_unreachable",
    503: "config_error",
    504: "timeout",
  };
  return map[status] ?? "internal_error";
}

/** User-facing Vietnamese message for UI */
export function formatChatApiError(error: unknown): string {
  if (error instanceof ChatApiError) {
    switch (error.code) {
      case "rate_limit":
        return error.message;
      case "auth_error":
        return `${error.message} (HTTP ${error.status})`;
      case "config_error":
      case "model_missing":
        return `${error.message} Khởi động lại backend sau khi sửa .env.`;
      case "upstream_unreachable":
        return `${error.message} Đảm bảo \`py api_server.py\` đang chạy và DEEPSEEK_BASE_URL đúng.`;
      case "timeout":
        return error.message;
      case "validation_error":
      case "bad_request":
        return error.message;
      case "invalid_provider":
        return error.message;
      default:
        if (error.status >= 500) {
          return `Lỗi máy chủ (${error.status}): ${error.message}`;
        }
        return error.message;
    }
  }

  if (error instanceof TypeError && String(error.message).toLowerCase().includes("fetch")) {
    return "Không kết nối được backend. Chạy py api_server.py (port 8000) và kiểm tra VITE_API_URL.";
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Lỗi không xác định";
}

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

export async function getApiHealth(): Promise<ApiHealth> {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (!res.ok) return { ok: false };
    const data = (await res.json()) as { provider?: string; model?: string };
    return { ok: true, provider: data.provider, model: data.model };
  } catch {
    return { ok: false };
  }
}

/** @deprecated use getApiHealth */
export async function checkApiHealth(): Promise<boolean> {
  const h = await getApiHealth();
  return h.ok;
}
