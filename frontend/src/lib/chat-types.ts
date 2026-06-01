import type { AgentStepRecord } from "@/lib/agent-activity";
import type { WeatherInfo } from "@/lib/dashboard-context";

export type ChatRole = "user" | "assistant";

export type TicketCard = {
  name: string;
  salePrice: number;
  salePriceFormatted: string;
  originalPrice?: number | null;
  originalPriceFormatted?: string | null;
  isCheapest?: boolean;
};

export type PriceQuote = {
  siteName: string;
  region?: string;
  supplierCode: string;
  usingDate: string;
  bookingUrl: string;
  cheapestTicketName?: string;
  cheapestFormatted?: string;
  tickets: TicketCard[];
};

export type ChatAction =
  | { id: string; label: string; kind: "link"; href: string }
  | { id: string; label: string; kind: "message"; text: string }
  | {
      id: string;
      label: string;
      kind: "tab";
      tab: "tickets";
      supplierCode?: string;
      usingDate?: string;
    };

export type MapMarker = {
  code: string;
  name: string;
  tag: string;
  lat: number;
  lng: number;
};

export type DestinationMap = {
  region: string;
  destinationCode: string;
  center: { lat: number; lng: number };
  zoom: number;
  bbox: number[];
  embedUrl: string;
  markers: MapMarker[];
  subLocationCount: number;
};

export type WeatherCardInfo = WeatherInfo;

export type ChatStructured = {
  priceQuote?: PriceQuote;
  weather?: WeatherInfo;
  destinationMap?: DestinationMap;
  actions?: ChatAction[];
};

export type AgentRunMeta = {
  steps: AgentStepRecord[];
  toolCount: number;
  reactSteps: number;
};

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  structured?: ChatStructured;
  agentRun?: AgentRunMeta;
};
