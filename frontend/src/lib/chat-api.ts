import type { AgentRunState, AgentStepRecord } from "@/lib/agent-activity";
import type { ChatMessage, AgentRunMeta, ChatStructured } from "./chat-types";
import type { DashboardContext } from "./dashboard-context";

const API_BASE = import.meta.env.VITE_VINWONDERS_API ?? "";

type ApiChatMessage = { role: "user" | "assistant" | "system"; content: string };

export type StreamChatCallbacks = {
  onDelta: (text: string) => void;
  onStructured?: (data: ChatStructured) => void;
  onDashboard?: (data: DashboardContext) => void;
  onAgentActivity?: (state: AgentRunState) => void;
  onAgentDone?: (run: AgentRunMeta) => void;
};

function toApiMessages(messages: ChatMessage[]): ApiChatMessage[] {
  return messages.map((m) => ({ role: m.role, content: m.content }));
}

export async function streamChat(
  messages: ChatMessage[],
  callbacks: StreamChatCallbacks,
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
  let gotContent = false;
  const activitySteps: AgentStepRecord[] = [];
  let toolCount = 0;

  const pushActivity = () => {
    callbacks.onAgentActivity?.({
      active: true,
      steps: [...activitySteps],
      toolCount,
      reactSteps: activitySteps.filter((s) => s.phase === "tool").length,
    });
  };

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
          data?: ChatStructured | DashboardContext;
          run?: AgentRunMeta;
          choices?: { delta?: { content?: string } }[];
          step?: AgentStepRecord;
        };

        if (chunk.type === "agent_step" && chunk.step) {
          const rec = chunk.step;
          const idx = activitySteps.findIndex((s) => s.id === rec.id);
          if (idx >= 0) {
            activitySteps[idx] = rec;
          } else {
            activitySteps.push(rec);
          }
          if (rec.phase === "tool" && rec.status === "done") {
            toolCount = activitySteps.filter(
              (s) =>
                s.phase === "tool" &&
                s.status === "done" &&
                s.title.startsWith("Observation"),
            ).length;
          }
          pushActivity();
          continue;
        }

        if (chunk.type === "agent_done" && chunk.run) {
          callbacks.onAgentDone?.(chunk.run);
          callbacks.onAgentActivity?.({
            active: false,
            steps: chunk.run.steps ?? activitySteps,
            toolCount: chunk.run.toolCount ?? toolCount,
            reactSteps: chunk.run.reactSteps ?? 0,
          });
          continue;
        }

        if (chunk.type === "structured" && chunk.data) {
          gotContent = true;
          callbacks.onStructured?.(chunk.data as ChatStructured);
          continue;
        }

        if (chunk.type === "dashboard" && chunk.data) {
          callbacks.onDashboard?.(chunk.data as DashboardContext);
          continue;
        }

        if (chunk.type === "error" && chunk.message) {
          if (gotContent) return;
          throw new Error(chunk.message);
        }

        const delta = chunk.choices?.[0]?.delta?.content;
        if (delta) {
          gotContent = true;
          callbacks.onDelta(delta);
        }
      } catch (err) {
        if (err instanceof SyntaxError) continue;
        throw err;
      }
    }
  }
}
