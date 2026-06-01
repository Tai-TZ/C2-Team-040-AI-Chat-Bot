/** Shared state between chat agent and right-hand canvas. */

import type { PriceQuote } from "@/lib/chat-types";

export type DashboardFocus = "idle" | "destination" | "weather" | "prices";

export type WeatherInfo = {
  location: string;
  usingDate: string;
  tempC?: number | null;
  feelsLikeC?: number | null;
  description?: string;
  icon?: string;
  humidity?: number;
  windMs?: number;
  popPercent?: number;
  hasRain?: boolean;
  rainRisk?: string;
  recommendation?: string;
  suggestReschedule?: boolean;
  nextDayDate?: string;
  nextDayHasRain?: boolean | null;
};

export type DestinationInfo = {
  region: string;
  siteName: string;
  supplierCode: string;
  usingDate: string;
};

export type DashboardContext = {
  focus: DashboardFocus;
  destination?: DestinationInfo;
  weather?: WeatherInfo;
  priceQuote?: PriceQuote;
};

export const IDLE_DASHBOARD: DashboardContext = { focus: "idle" };

const EVENT = "vinwonders:dashboard";

export function dispatchDashboardContext(ctx: DashboardContext) {
  window.dispatchEvent(new CustomEvent(EVENT, { detail: ctx }));
}

export function subscribeDashboardContext(
  handler: (ctx: DashboardContext) => void,
): () => void {
  const listener = (e: Event) => {
    handler((e as CustomEvent<DashboardContext>).detail);
  };
  window.addEventListener(EVENT, listener);
  return () => window.removeEventListener(EVENT, listener);
}
