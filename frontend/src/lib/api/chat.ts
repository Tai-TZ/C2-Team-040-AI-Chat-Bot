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

const API_BASE = import.meta.env.VITE_API_URL ?? "";

export async function sendChatMessage(
  message: string,
  mode: ChatMode = "agent",
): Promise<ChatApiResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, mode, provider: "deepseek" }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = (body as { detail?: string }).detail ?? res.statusText;
    throw new Error(detail || "Không thể kết nối tới AI server");
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
