/** Live agent activity bus — chat ↔ right panel "Agent hoạt động". */

export type AgentStepPhase =
  | "init"
  | "reasoning"
  | "tool"
  | "react"
  | "summarize";

export type AgentStepStatus = "running" | "done" | "error";

export type AgentStepSource = "bootstrap" | "model" | "system";

export type AgentStepRecord = {
  id: string;
  phase: AgentStepPhase;
  title: string;
  detail?: string;
  tool?: string;
  args?: Record<string, string>;
  observationPreview?: string;
  status: AgentStepStatus;
  source: AgentStepSource;
};

export type AgentRunState = {
  active: boolean;
  steps: AgentStepRecord[];
  toolCount: number;
  reactSteps: number;
};

export const IDLE_AGENT_RUN: AgentRunState = {
  active: false,
  steps: [],
  toolCount: 0,
  reactSteps: 0,
};

const EVENT = "vinwonders:agent-activity";

export function dispatchAgentActivity(state: AgentRunState) {
  window.dispatchEvent(new CustomEvent(EVENT, { detail: state }));
}

export function subscribeAgentActivity(
  handler: (state: AgentRunState) => void,
): () => void {
  const listener = (e: Event) => {
    handler((e as CustomEvent<AgentRunState>).detail);
  };
  window.addEventListener(EVENT, listener);
  return () => window.removeEventListener(EVENT, listener);
}
