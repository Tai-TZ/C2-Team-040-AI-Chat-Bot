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
}

const API_BASE = import.meta.env.VITE_API_URL ?? "";

export async function sendChatMessage(
  message: string,
  mode: ChatMode = "agent",
): Promise<ChatApiResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, mode }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = (body as { detail?: string }).detail ?? res.statusText;
    throw new Error(detail || "Không thể kết nối tới AI server");
  }

  return res.json() as Promise<ChatApiResponse>;
}

export async function checkApiHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    return res.ok;
  } catch {
    return false;
  }
}
