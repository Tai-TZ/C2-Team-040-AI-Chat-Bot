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

export type ChatStructured = {
  priceQuote?: PriceQuote;
  actions?: ChatAction[];
};

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  structured?: ChatStructured;
};
