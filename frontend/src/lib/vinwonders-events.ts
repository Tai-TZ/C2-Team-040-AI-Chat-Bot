/** Cross-panel events between chat and canvas. */

export type OpenTicketsTabDetail = {
  supplierCode?: string;
  /** DD-MM-YYYY from API */
  usingDate?: string;
};

const OPEN_TICKETS = "vinwonders:open-tickets";

export function dispatchOpenTicketsTab(detail: OpenTicketsTabDetail) {
  window.dispatchEvent(new CustomEvent(OPEN_TICKETS, { detail }));
}

export function subscribeOpenTicketsTab(
  handler: (detail: OpenTicketsTabDetail) => void,
): () => void {
  const listener = (e: Event) => {
    handler((e as CustomEvent<OpenTicketsTabDetail>).detail);
  };
  window.addEventListener(OPEN_TICKETS, listener);
  return () => window.removeEventListener(OPEN_TICKETS, listener);
}

/** DD-MM-YYYY → YYYY-MM-DD for <input type="date"> */
export function usingDateToIso(usingDate: string): string {
  const m = usingDate.match(/^(\d{2})-(\d{2})-(\d{4})$/);
  if (!m) return usingDate;
  return `${m[3]}-${m[2]}-${m[1]}`;
}
