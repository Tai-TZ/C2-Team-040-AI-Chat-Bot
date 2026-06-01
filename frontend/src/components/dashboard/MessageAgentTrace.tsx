import { useState } from "react";
import { ChevronDown, ChevronUp, Workflow } from "lucide-react";
import type { AgentStepRecord } from "@/lib/agent-activity";

type Props = {
  steps: AgentStepRecord[];
  toolCount: number;
};

export function MessageAgentTrace({ steps, toolCount }: Props) {
  const [open, setOpen] = useState(false);
  if (steps.length === 0) return null;

  return (
    <div className="mt-3 rounded-xl border border-violet-500/25 bg-violet-500/5">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-xs font-medium text-foreground"
      >
        <span className="inline-flex items-center gap-1.5">
          <Workflow className="h-3.5 w-3.5 text-violet-600" />
          Quy trình Agent ({toolCount} tools · {steps.length} bước)
        </span>
        {open ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </button>
      {open && (
        <ul className="max-h-48 space-y-1.5 overflow-y-auto border-t border-violet-500/15 px-3 py-2 scrollbar-thin">
          {steps.map((s) => (
            <li
              key={s.id}
              className="rounded-lg bg-background/60 px-2 py-1.5 text-[11px]"
            >
              <span className="font-semibold text-violet-700 dark:text-violet-300">
                {s.title}
              </span>
              {s.detail && (
                <span className="text-muted-foreground"> — {s.detail}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
