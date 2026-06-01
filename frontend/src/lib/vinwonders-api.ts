import type { DestinationsResponse, PricesResponse } from "./vinwonders-types";

const API_BASE = import.meta.env.VITE_VINWONDERS_API ?? "";

export function formatVnd(amount: number): string {
  return new Intl.NumberFormat("vi-VN").format(amount) + "₫";
}

/** YYYY-MM-DD (input) → DD-MM-YYYY (VinWonders API) */
export function toApiDate(isoDate: string): string {
  const [y, m, d] = isoDate.split("-");
  return `${d}-${m}-${y}`;
}

export async function fetchDestinations(): Promise<DestinationsResponse> {
  const res = await fetch(`${API_BASE}/api/destinations`);
  if (!res.ok) throw new Error("Không tải được danh sách địa điểm");
  return res.json();
}

export async function fetchTicketPrices(
  code: string,
  isoDate: string,
): Promise<PricesResponse> {
  const params = new URLSearchParams({
    code,
    date: toApiDate(isoDate),
  });
  const res = await fetch(`${API_BASE}/api/prices?${params}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      (body as { detail?: string }).detail ?? "Không lấy được giá vé",
    );
  }
  return res.json();
}
