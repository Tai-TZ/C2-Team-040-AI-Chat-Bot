import { useEffect, useMemo, useState } from "react";
import type { AgentProgress } from "@/components/dashboard/AILoadingState";
import {
  LOADING_STEP_MS,
  buildScriptedStages,
  extractLocationFromQuery,
} from "@/lib/ai-loading-script";

/** Advances hardcoded loading copy every 12s while `active`. */
export function useScriptedAgentLoading(
  active: boolean,
  userQuery: string,
): AgentProgress | null {
  const location = useMemo(
    () => extractLocationFromQuery(userQuery),
    [userQuery],
  );
  const stages = useMemo(
    () => buildScriptedStages(location),
    [location],
  );
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    if (!active) {
      setStepIndex(0);
      return;
    }
    setStepIndex(0);
    const timers = stages.slice(1).map((_, i) =>
      window.setTimeout(() => setStepIndex(i + 1), LOADING_STEP_MS * (i + 1)),
    );
    return () => timers.forEach((id) => window.clearTimeout(id));
  }, [active, stages, userQuery]);

  if (!active) return null;

  const idx = Math.min(stepIndex, stages.length - 1);
  const stage = stages[idx];
  return {
    status: stage.status,
    lines: stages.slice(0, idx + 1).map((s) => s.line),
    progress: stage.progress,
    phase: stage.phase,
  };
}
