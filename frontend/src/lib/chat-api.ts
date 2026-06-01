import type { ChatMessage, ChatStructured } from "./chat-types";

const API_BASE = import.meta.env.VITE_VINWONDERS_API ?? "";

type ApiChatMessage = { role: "user" | "assistant" | "system"; content: string };

function toApiMessages(messages: ChatMessage[]): ApiChatMessage[] {
  return messages.map((m) => ({ role: m.role, content: m.content }));
}

export async function streamChat(
  messages: ChatMessage[],
  onDelta: (text: string) => void,
  onTrace?: (message: string) => void,
  onStructured?: (data: ChatStructured) => void,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages: toApiMessages(messages), stream: true }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(
      (err as { detail?: string }).detail ?? `Chat failed (${res.status})`,
    );
  }

  if (!res.body) {
    throw new Error("No response body");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data:")) continue;
      const data = trimmed.slice(5).trim();
      if (data === "[DONE]") return;

      try {
        const chunk = JSON.parse(data) as {
          type?: string;
          message?: string;
          data?: ChatStructured;
          choices?: { delta?: { content?: string } }[];
        };
        if (chunk.type === "structured" && chunk.data) {
          onStructured?.(chunk.data);
          continue;
        }
        if (chunk.type === "trace" && chunk.message) {
          onTrace?.(chunk.message);
          continue;
        }
        if (chunk.type === "error" && chunk.message) {
          throw new Error(chunk.message);
        }
        const delta = chunk.choices?.[0]?.delta?.content;
        if (delta) onDelta(delta);
      } catch (err) {
        if (err instanceof SyntaxError) continue;
        throw err;
      }
    }
  }
}
