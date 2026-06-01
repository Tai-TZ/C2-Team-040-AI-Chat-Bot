import { useCallback, useEffect, useRef, useState } from "react";
import {
  Sparkles,
  Send,
  User,
  Plane,
  Ticket,
  Calendar,
  Loader2,
} from "lucide-react";
import {
  AILoadingState,
  type AgentProgress,
} from "@/components/dashboard/AILoadingState";
import { AssistantMessage } from "@/components/dashboard/AssistantMessage";
import { streamChat } from "@/lib/chat-api";
import type { ChatAction, ChatMessage } from "@/lib/chat-types";
import { dispatchDashboardContext } from "@/lib/dashboard-context";

const quickActions = [
  { label: "Lên kế hoạch cuối tuần", icon: Calendar },
  { label: "Đặt vé Tata Show", icon: Ticket },
  { label: "Săn vé máy bay", icon: Plane },
];

function newId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

const WELCOME: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Xin chào! Tôi là VinWonders Tour Guide AI. Bạn có thể hỏi về lịch trình, combo vé, hoặc sang tab Vé & Chuyến bay bên phải để xem giá vé theo ngày. Bạn muốn đi đâu?",
};

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [agentProgress, setAgentProgress] = useState<AgentProgress | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, agentProgress, scrollToBottom]);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || loading) return;

      const userMsg: ChatMessage = {
        id: newId(),
        role: "user",
        content: trimmed,
      };
      const history = [...messages.filter((m) => m.id !== "welcome"), userMsg];
      const assistantId = newId();

      setMessages([...messages.filter((m) => m.id !== "welcome"), userMsg]);
      setInput("");
      setLoading(true);
      setAgentProgress({
        status: "Đang khởi động agent...",
        lines: ["Nhận câu hỏi của bạn...", "Khởi tạo VinWonders Tour Guide Agent..."],
        progress: 8,
      });
      setError(null);

      setMessages((prev) => [
        ...prev,
        { id: assistantId, role: "assistant", content: "" },
      ]);

      try {
        await streamChat(
          history,
          (delta) => {
            setAgentProgress(null);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: m.content + delta }
                  : m,
              ),
            );
          },
          (trace) => setAgentProgress(trace),
          (structured) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, structured } : m,
              ),
            );
          },
          (dashboard) => {
            dispatchDashboardContext(dashboard);
          },
        );
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Lỗi kết nối AI";
        setError(msg);
        setMessages((prev) => prev.filter((m) => m.id !== assistantId));
      } finally {
        setLoading(false);
        setAgentProgress(null);
      }
    },
    [loading, messages],
  );

  function handleNewChat() {
    setMessages([WELCOME]);
    setError(null);
    setInput("");
    dispatchDashboardContext({ focus: "idle" });
  }

  function handleMessageAction(action: ChatAction) {
    if (action.kind === "message") {
      sendMessage(action.text);
    }
  }

  return (
    <div className="flex h-full flex-col bg-surface">
      <header className="flex items-center justify-between border-b border-border px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="relative grid h-10 w-10 place-items-center rounded-xl bg-gradient-primary shadow-glow">
            <Sparkles className="h-5 w-5 text-primary-foreground" strokeWidth={2.4} />
          </div>
          <div>
            <h1 className="text-sm font-semibold tracking-tight text-foreground">
              VinWonders Tour Guide
            </h1>
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span
                className={`h-1.5 w-1.5 rounded-full ${loading ? "bg-amber-400 animate-pulse" : "bg-success animate-pulse"}`}
              />
              AI Concierge · {loading ? "Đang trả lời..." : "Trực tuyến"}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleNewChat}
          disabled={loading}
          className="rounded-full border border-border bg-background px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted disabled:opacity-50"
        >
          Hội thoại mới
        </button>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto scrollbar-thin px-5 py-6">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex animate-fade-in-up ${m.role === "user" ? "justify-end" : "gap-2"}`}
          >
            {m.role === "assistant" && (
              <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-gradient-primary text-primary-foreground shadow-soft">
                <Sparkles className="h-4 w-4" />
              </div>
            )}
            <div
              className={`text-sm leading-relaxed ${
                m.role === "user"
                  ? "max-w-[85%] rounded-2xl rounded-br-md bg-gradient-primary px-4 py-3 text-primary-foreground shadow-soft"
                  : "max-w-[min(100%,28rem)] rounded-2xl rounded-tl-md border border-border bg-card px-4 py-3 text-card-foreground shadow-soft"
              }`}
            >
              {m.role === "assistant" && !m.content && loading && agentProgress ? (
                <AILoadingState progress={agentProgress} />
              ) : m.role === "assistant" && !m.content && loading ? (
                <span className="inline-flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Agent đang kết nối...
                </span>
              ) : m.role === "assistant" ? (
                <AssistantMessage
                  message={m}
                  onAction={handleMessageAction}
                />
              ) : (
                <p className="whitespace-pre-wrap">{m.content}</p>
              )}
            </div>
            {m.role === "user" && (
              <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-muted text-muted-foreground">
                <User className="h-4 w-4" />
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {error && (
        <div className="mx-5 mb-2 rounded-xl border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
          {error}
          <p className="mt-1 text-muted-foreground">
            Kiểm tra backend{" "}
            <code className="rounded bg-muted px-1">python -m src.vinwonders.server</code>{" "}
            và <code className="rounded bg-muted px-1">DS2API_API_KEY</code> trong file{" "}
            <code className="rounded bg-muted px-1">.env</code>.
          </p>
        </div>
      )}

      <div className="border-t border-border bg-surface-elevated/60 px-5 py-4 backdrop-blur">
        <div className="mb-3 flex flex-wrap gap-2">
          {quickActions.map((a) => (
            <button
              key={a.label}
              type="button"
              disabled={loading}
              onClick={() => sendMessage(a.label)}
              className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1.5 text-xs font-medium text-foreground transition-all hover:border-primary hover:bg-accent disabled:opacity-50"
            >
              <a.icon className="h-3.5 w-3.5" />
              {a.label}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage(input);
          }}
          className="flex items-center gap-2 rounded-2xl border border-border bg-background p-2 shadow-soft transition-all focus-within:border-primary focus-within:shadow-glow"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder="Hỏi gì đó về chuyến đi của bạn..."
            className="flex-1 bg-transparent px-2 py-1.5 text-sm placeholder:text-muted-foreground focus:outline-none disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-primary text-primary-foreground transition-transform hover:scale-105 active:scale-95 disabled:opacity-50"
            aria-label="Gửi"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
