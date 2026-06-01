import { useCallback, useEffect, useState } from "react";
import {
  Sparkles,
  Send,
  ChevronDown,
  User,
  Plane,
  Ticket,
  Calendar,
  Loader2,
} from "lucide-react";
import {
  getApiHealth,
  sendChatMessage,
  type ChatMessage,
} from "@/lib/api/chat";

const quickActions = [
  { label: "Lên kế hoạch cuối tuần", icon: Calendar },
  { label: "Đặt vé Tata Show", icon: Ticket },
  { label: "Săn vé máy bay", icon: Plane },
];

const WELCOME: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Xin chào! Tôi là AI Concierge VinWonders. Hỏi tôi về lịch trình, vé, giá cả hoặc gợi ý chuyến đi Phú Quốc nhé.",
};

function newId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function ChatPanel({ onSend }: { onSend?: (msg: string) => void }) {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME]);
  const [openReasoning, setOpenReasoning] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [apiProvider, setApiProvider] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getApiHealth().then((h) => {
      setApiOnline(h.ok);
      setApiProvider(h.provider ?? null);
    });
  }, []);

  const handleSend = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || loading) return;

      onSend?.(trimmed);
      setError(null);

      const userMsg: ChatMessage = { id: newId(), role: "user", content: trimmed };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setLoading(true);

      try {
        const data = await sendChatMessage(trimmed, "agent");
        const assistantMsg: ChatMessage = {
          id: newId(),
          role: "assistant",
          content: data.reply,
          reasoningSteps: data.reasoning_steps.length > 0 ? data.reasoning_steps : undefined,
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (e) {
        const raw = e instanceof Error ? e.message : "Lỗi không xác định";
        const isQuota =
          raw.includes("429") ||
          raw.includes("quota") ||
          raw.includes("insufficient_quota") ||
          raw.includes("RESOURCE_EXHAUSTED");
        const msg = isQuota
          ? `API hết quota (provider: ${apiProvider ?? "unknown"}). Đang dùng DeepSeek? Kiểm tra DEFAULT_PROVIDER=deepseek trong .env và restart backend.`
          : raw;
        setError(msg);
        setMessages((prev) => [
          ...prev,
          {
            id: newId(),
            role: "assistant",
            content: `Xin lỗi, không thể trả lời.\n\n${msg}`,
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [loading, onSend],
  );

  const resetChat = () => {
    setMessages([WELCOME]);
    setOpenReasoning(null);
    setError(null);
  };

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
                className={`h-1.5 w-1.5 rounded-full ${
                  apiOnline === false ? "bg-destructive" : "bg-success animate-pulse"
                }`}
              />
              {apiOnline === false
                ? "Offline · Chạy py api_server.py"
                : `AI Concierge · ${apiProvider ?? "deepseek"}`}
            </p>
          </div>
        </div>
        <button
          onClick={resetChat}
          disabled={loading}
          className="rounded-full border border-border bg-background px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted disabled:opacity-50"
        >
          Hội thoại mới
        </button>
      </header>

      <div className="flex-1 space-y-6 overflow-y-auto scrollbar-thin px-5 py-6">
        {messages.map((msg) =>
          msg.role === "user" ? (
            <div key={msg.id} className="flex justify-end animate-fade-in-up">
              <div className="flex max-w-[85%] items-end gap-2">
                <div className="rounded-2xl rounded-br-md bg-gradient-primary px-4 py-3 text-sm text-primary-foreground shadow-soft whitespace-pre-wrap">
                  {msg.content}
                </div>
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-muted text-muted-foreground">
                  <User className="h-4 w-4" />
                </div>
              </div>
            </div>
          ) : (
            <div key={msg.id} className="flex animate-fade-in-up gap-2">
              <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-gradient-primary text-primary-foreground shadow-soft">
                <Sparkles className="h-4 w-4" />
              </div>
              <div className="flex-1 space-y-3 min-w-0">
                {msg.reasoningSteps && msg.reasoningSteps.length > 0 && (
                  <>
                    <button
                      onClick={() =>
                        setOpenReasoning((v) => (v === msg.id ? null : msg.id))
                      }
                      className="group inline-flex items-center gap-2 rounded-full border border-border bg-muted/60 px-3 py-1.5 text-xs font-medium text-muted-foreground transition-all hover:bg-muted"
                    >
                      <Loader2 className="h-3 w-3 text-primary" />
                      <span>Agent reasoning · {msg.reasoningSteps.length} bước</span>
                      <ChevronDown
                        className={`h-3 w-3 transition-transform ${openReasoning === msg.id ? "rotate-180" : ""}`}
                      />
                    </button>
                    {openReasoning === msg.id && (
                      <div className="animate-scale-in rounded-2xl border border-border bg-muted/40 p-3">
                        <ol className="space-y-2">
                          {msg.reasoningSteps.map((step, i) => (
                            <li
                              key={i}
                              className="flex items-start gap-2.5 text-xs text-muted-foreground"
                            >
                              <span className="mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded-full bg-primary/15 text-[10px] font-semibold text-primary">
                                {i + 1}
                              </span>
                              <span>{step}</span>
                            </li>
                          ))}
                        </ol>
                      </div>
                    )}
                  </>
                )}
                <div className="rounded-2xl rounded-tl-md bg-card border border-border px-4 py-3 text-sm leading-relaxed text-card-foreground shadow-soft whitespace-pre-wrap">
                  {msg.content}
                </div>
              </div>
            </div>
          ),
        )}

        {loading && (
          <div className="flex gap-2 items-center text-xs text-muted-foreground animate-pulse px-2">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            AI đang suy nghĩ...
          </div>
        )}
      </div>

      <div className="border-t border-border bg-surface-elevated/60 backdrop-blur px-5 py-4">
        {error && (
          <p className="mb-2 text-xs text-destructive">{error}</p>
        )}
        <div className="mb-3 flex flex-wrap gap-2">
          {quickActions.map((a) => (
            <button
              key={a.label}
              type="button"
              disabled={loading}
              onClick={() => handleSend(a.label)}
              className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1.5 text-xs font-medium text-foreground transition-all hover:border-primary hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
            >
              <a.icon className="h-3.5 w-3.5" />
              {a.label}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend(input);
          }}
          className="flex items-center gap-2 rounded-2xl border border-border bg-background p-2 shadow-soft focus-within:border-primary focus-within:shadow-glow transition-all"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder="Hỏi gì đó về chuyến đi của bạn..."
            className="flex-1 bg-transparent px-2 py-1.5 text-sm placeholder:text-muted-foreground focus:outline-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-primary text-primary-foreground transition-transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
            aria-label="Send"
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
