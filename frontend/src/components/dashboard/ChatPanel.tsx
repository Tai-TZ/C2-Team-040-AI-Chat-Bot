import { useState } from "react";
import { Sparkles, Send, ChevronDown, User, Plane, Ticket, Calendar, Loader2 } from "lucide-react";
import { reasoningSteps } from "@/lib/mock-data";

const quickActions = [
  { label: "Lên kế hoạch cuối tuần", icon: Calendar },
  { label: "Đặt vé Tata Show", icon: Ticket },
  { label: "Săn vé máy bay", icon: Plane },
];

export function ChatPanel({ onSend }: { onSend?: (msg: string) => void }) {
  const [openReasoning, setOpenReasoning] = useState(false);
  const [input, setInput] = useState("");

  return (
    <div className="flex h-full flex-col bg-surface">
      {/* Header */}
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
              <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
              AI Concierge · Trực tuyến
            </p>
          </div>
        </div>
        <button className="rounded-full border border-border bg-background px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted">
          Hội thoại mới
        </button>
      </header>

      {/* Messages */}
      <div className="flex-1 space-y-6 overflow-y-auto scrollbar-thin px-5 py-6">
        {/* User message */}
        <div className="flex justify-end animate-fade-in-up">
          <div className="flex max-w-[85%] items-end gap-2">
            <div className="rounded-2xl rounded-br-md bg-gradient-primary px-4 py-3 text-sm text-primary-foreground shadow-soft">
              Tôi muốn đi du lịch VinWonders vào cuối tuần này từ Hà Nội vào Phú Quốc
            </div>
            <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-muted text-muted-foreground">
              <User className="h-4 w-4" />
            </div>
          </div>
        </div>

        {/* AI message */}
        <div className="flex animate-fade-in-up gap-2" style={{ animationDelay: "100ms" }}>
          <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-gradient-primary text-primary-foreground shadow-soft">
            <Sparkles className="h-4 w-4" />
          </div>
          <div className="flex-1 space-y-3">
            {/* Reasoning chain */}
            <button
              onClick={() => setOpenReasoning((v) => !v)}
              className="group inline-flex items-center gap-2 rounded-full border border-border bg-muted/60 px-3 py-1.5 text-xs font-medium text-muted-foreground transition-all hover:bg-muted"
            >
              <Loader2 className="h-3 w-3 text-primary" />
              <span>Agent reasoning · {reasoningSteps.length} bước</span>
              <ChevronDown
                className={`h-3 w-3 transition-transform ${openReasoning ? "rotate-180" : ""}`}
              />
            </button>

            {openReasoning && (
              <div className="animate-scale-in rounded-2xl border border-border bg-muted/40 p-3">
                <ol className="space-y-2">
                  {reasoningSteps.map((step, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-xs text-muted-foreground">
                      <span className="mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded-full bg-primary/15 text-[10px] font-semibold text-primary">
                        {i + 1}
                      </span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}

            <div className="rounded-2xl rounded-tl-md bg-card border border-border px-4 py-3 text-sm leading-relaxed text-card-foreground shadow-soft">
              Tuyệt vời! Tôi đã lên kế hoạch <span className="font-semibold text-primary">2 ngày 1 đêm </span>
              tại Phú Quốc cho bạn. Bay sáng thứ Bảy, ghé Vinpearl Safari, xem{" "}
              <span className="font-semibold">Tata Show</span> tối, và khám phá VinWonders cả ngày Chủ Nhật.
              <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                <Stat label="Tổng chi phí" value="6.4tr₫" />
                <Stat label="Điểm đến" value="5" />
                <Stat label="Tiết kiệm" value="–22%" tone="success" />
              </div>
              <p className="mt-3 text-xs text-muted-foreground">
                👉 Xem chi tiết ở canvas bên phải — lịch trình, vé bay, sự kiện.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-border bg-surface-elevated/60 backdrop-blur px-5 py-4">
        <div className="mb-3 flex flex-wrap gap-2">
          {quickActions.map((a) => (
            <button
              key={a.label}
              onClick={() => onSend?.(a.label)}
              className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1.5 text-xs font-medium text-foreground transition-all hover:border-primary hover:bg-accent hover:text-accent-foreground"
            >
              <a.icon className="h-3.5 w-3.5" />
              {a.label}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (input.trim()) {
              onSend?.(input);
              setInput("");
            }
          }}
          className="flex items-center gap-2 rounded-2xl border border-border bg-background p-2 shadow-soft focus-within:border-primary focus-within:shadow-glow transition-all"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Hỏi gì đó về chuyến đi của bạn..."
            className="flex-1 bg-transparent px-2 py-1.5 text-sm placeholder:text-muted-foreground focus:outline-none"
          />
          <button
            type="submit"
            className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-primary text-primary-foreground transition-transform hover:scale-105 active:scale-95"
            aria-label="Send"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: "success" }) {
  return (
    <div className="rounded-xl bg-muted/60 p-2">
      <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className={`text-sm font-semibold ${tone === "success" ? "text-success" : "text-foreground"}`}>
        {value}
      </p>
    </div>
  );
}
