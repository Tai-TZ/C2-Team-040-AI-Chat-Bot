import {
  Bot,
  Brain,
  CheckCircle2,
  Circle,
  Loader2,
  Wrench,
  XCircle,
} from "lucide-react";
import type { AgentRunState, AgentStepRecord } from "@/lib/agent-activity";

function StepIcon({ step }: { step: AgentStepRecord }) {
  if (step.status === "running") {
    return <Loader2 className="h-4 w-4 shrink-0 animate-spin text-primary" />;
  }
  if (step.status === "error") {
    return <XCircle className="h-4 w-4 shrink-0 text-destructive" />;
  }
  if (step.phase === "tool") {
    return <Wrench className="h-4 w-4 shrink-0 text-primary" />;
  }
  if (step.phase === "reasoning" || step.phase === "react") {
    return <Brain className="h-4 w-4 shrink-0 text-violet-500" />;
  }
  return <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />;
}

function sourceLabel(source: AgentStepRecord["source"]) {
  if (source === "bootstrap") return "Auto pipeline";
  if (source === "model") return "ReAct (LLM)";
  return "Hệ thống";
}

type Props = {
  run: AgentRunState;
};

export function AgentActivityPanel({ run }: Props) {
  const steps = run.steps;

  return (
    <div className="space-y-4 animate-fade-in-up">
      <div className="rounded-2xl border border-primary/25 bg-gradient-to-r from-primary/10 to-violet-500/10 p-4">
        <div className="flex items-start gap-3">
          <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/15 text-primary">
            <Bot className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="text-base font-bold text-foreground">
              ReAct Agent đang hoạt động
            </h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Thought → Action → Observation — không phải chatbot một lượt.
            </p>
            <div className="mt-2 flex flex-wrap gap-2 text-[11px]">
              <span className="rounded-full bg-background/80 px-2 py-0.5 font-medium">
                {run.toolCount} tool calls
              </span>
              <span className="rounded-full bg-background/80 px-2 py-0.5 font-medium">
                {run.reactSteps} bước trace
              </span>
              <span
                className={`rounded-full px-2 py-0.5 font-semibold ${
                  run.active
                    ? "bg-amber-500/15 text-amber-700 dark:text-amber-300"
                    : "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300"
                }`}
              >
                {run.active ? "Đang chạy…" : "Hoàn tất"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {steps.length === 0 ? (
        <p className="rounded-2xl border border-dashed border-border bg-card/50 p-6 text-center text-sm text-muted-foreground">
          Gửi câu hỏi trong chat — timeline Thought / Action / Observation sẽ
          hiện tại đây theo thời gian thực.
        </p>
      ) : (
        <ol className="relative space-y-0 border-l-2 border-primary/20 pl-4">
          {steps.map((step, i) => (
            <li key={step.id} className="relative pb-5 last:pb-0">
              <Circle
                className={`absolute -left-[1.35rem] top-1 h-2.5 w-2.5 fill-current ${
                  step.status === "running"
                    ? "text-primary animate-pulse"
                    : step.status === "error"
                      ? "text-destructive"
                      : "text-emerald-500"
                }`}
              />
              <div
                className={`rounded-xl border px-3 py-2.5 transition-colors ${
                  step.status === "running"
                    ? "border-primary/40 bg-primary/5 shadow-soft"
                    : "border-border bg-card/80"
                }`}
              >
                <div className="flex items-start gap-2">
                  <StepIcon step={step} />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-xs font-semibold text-foreground">
                        {step.title}
                      </span>
                      <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                        {sourceLabel(step.source)}
                      </span>
                    </div>
                    {step.detail && (
                      <p className="mt-1 text-[11px] leading-snug text-muted-foreground">
                        {step.detail}
                      </p>
                    )}
                    {step.tool && step.args && Object.keys(step.args).length > 0 && (
                      <pre className="mt-2 max-h-20 overflow-auto rounded-lg bg-muted/60 p-2 font-mono text-[10px] text-foreground/80">
                        {step.tool}(
                        {Object.entries(step.args)
                          .map(([k, v]) => `${k}="${v}"`)
                          .join(", ")}
                        )
                      </pre>
                    )}
                    {step.observationPreview && (
                      <p className="mt-1.5 border-l-2 border-emerald-500/40 pl-2 text-[11px] text-foreground/85">
                        <span className="font-medium text-emerald-600 dark:text-emerald-400">
                          Observation:{" "}
                        </span>
                        {step.observationPreview}
                      </p>
                    )}
                  </div>
                </div>
              </div>
              {i < steps.length - 1 && step.status === "done" && (
                <div className="ml-1 mt-1 text-[10px] text-muted-foreground/70">
                  ↓
                </div>
              )}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
