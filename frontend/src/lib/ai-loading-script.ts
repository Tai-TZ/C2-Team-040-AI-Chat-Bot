/** Hardcoded AI loading stages (12s per step) for demo / BGK presentation. */

import { matchDestinationInText } from "@/lib/destination-names";

export const LOADING_STEP_MS = 12_000;

export type ScriptedLoadingStage = {
  status: string;
  line: string;
  progress: number;
  phase: "init" | "tool";
};

export function extractLocationFromQuery(query: string): string {
  return matchDestinationInText(query);
}

export function buildScriptedStages(location: string): ScriptedLoadingStage[] {
  return [
    {
      status: "Đang kết nối agent...",
      line: "Đang kết nối agent...",
      progress: 10,
      phase: "init",
    },
    {
      status: `Kiểm tra thời tiết tại ${location}..`,
      line: `Kiểm tra thời tiết tại ${location}..`,
      progress: 35,
      phase: "tool",
    },
    {
      status: "Thời tiết ở đó đang....",
      line: "Thời tiết ở đó đang....",
      progress: 60,
      phase: "tool",
    },
    {
      status: "Đang contact với VinWonders...",
      line: "Đang contact với VinWonders...",
      progress: 85,
      phase: "tool",
    },
  ];
}
