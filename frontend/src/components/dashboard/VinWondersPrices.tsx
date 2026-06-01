import { useEffect, useMemo, useState } from "react";
import { Calendar, Loader2, MapPin, Search, Ticket } from "lucide-react";
import {
  fetchDestinations,
  fetchTicketPrices,
  formatVnd,
} from "@/lib/vinwonders-api";
import {
  subscribeOpenTicketsTab,
  usingDateToIso,
} from "@/lib/vinwonders-events";
import type { Destination, PricesResponse } from "@/lib/vinwonders-types";

function defaultIsoDate(): string {
  const d = new Date();
  d.setDate(d.getDate() + 7);
  return d.toISOString().slice(0, 10);
}

export function VinWondersPrices() {
  const [destinations, setDestinations] = useState<Destination[]>([]);
  const [loadingMeta, setLoadingMeta] = useState(true);
  const [metaError, setMetaError] = useState<string | null>(null);

  const [regionCode, setRegionCode] = useState("");
  const [siteCode, setSiteCode] = useState("");
  const [visitDate, setVisitDate] = useState(defaultIsoDate);

  const [loadingPrices, setLoadingPrices] = useState(false);
  const [priceError, setPriceError] = useState<string | null>(null);
  const [prices, setPrices] = useState<PricesResponse | null>(null);
  const [autoSearch, setAutoSearch] = useState(false);

  useEffect(() => {
    fetchDestinations()
      .then((data) => {
        const list = data.destinations ?? [];
        setDestinations(list);
        if (list.length > 0) {
          setRegionCode(list[0].destination_code);
          setSiteCode(list[0].sub_locations[0]?.code ?? "");
        }
      })
      .catch((e: Error) => setMetaError(e.message))
      .finally(() => setLoadingMeta(false));
  }, []);

  const region = useMemo(
    () => destinations.find((d) => d.destination_code === regionCode),
    [destinations, regionCode],
  );

  const sites = region?.sub_locations ?? [];

  useEffect(() => {
    if (!sites.some((s) => s.code === siteCode)) {
      setSiteCode(sites[0]?.code ?? "");
    }
  }, [sites, siteCode]);

  useEffect(() => {
    return subscribeOpenTicketsTab((detail) => {
      if (!detail.supplierCode || destinations.length === 0) return;
      const regionMatch = destinations.find((d) =>
        d.sub_locations.some((s) => s.code === detail.supplierCode),
      );
      if (regionMatch) setRegionCode(regionMatch.destination_code);
      setSiteCode(detail.supplierCode);
      if (detail.usingDate) setVisitDate(usingDateToIso(detail.usingDate));
      setAutoSearch(true);
    });
  }, [destinations]);

  const selectedSite = sites.find((s) => s.code === siteCode);

  async function handleSearch() {
    if (!siteCode || !visitDate) return;
    setLoadingPrices(true);
    setPriceError(null);
    setPrices(null);
    try {
      const result = await fetchTicketPrices(siteCode, visitDate);
      setPrices(result);
    } catch (e) {
      setPriceError(e instanceof Error ? e.message : "Lỗi không xác định");
    } finally {
      setLoadingPrices(false);
    }
  }

  useEffect(() => {
    if (!autoSearch || !siteCode || !visitDate) return;
    setAutoSearch(false);
    void handleSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- trigger once after chat prefill
  }, [autoSearch, siteCode, visitDate]);

  if (loadingMeta) {
    return (
      <div className="flex items-center justify-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Đang tải địa điểm...
      </div>
    );
  }

  if (metaError) {
    return (
      <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
        {metaError}
        <p className="mt-2 text-xs text-muted-foreground">
          Hãy chạy API:{" "}
          <code className="rounded bg-muted px-1">python -m src.vinwonders.server</code>
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-border bg-card p-4 shadow-soft">
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
          <Ticket className="h-4 w-4 text-primary" />
          Tra cứu giá vé VinWonders
        </h3>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-muted-foreground">
              Khu vực
            </span>
            <select
              value={regionCode}
              onChange={(e) => setRegionCode(e.target.value)}
              className="w-full rounded-xl border border-border bg-background px-3 py-2 text-sm"
            >
              {destinations.map((d) => (
                <option key={d.destination_code} value={d.destination_code}>
                  {d.destination_name}
                </option>
              ))}
            </select>
          </label>

          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-muted-foreground">
              Địa điểm vui chơi
            </span>
            <select
              value={siteCode}
              onChange={(e) => setSiteCode(e.target.value)}
              className="w-full rounded-xl border border-border bg-background px-3 py-2 text-sm"
            >
              {sites.map((s) => (
                <option key={s.code} value={s.code}>
                  {s.name} ({s.code})
                </option>
              ))}
            </select>
          </label>

          <label className="block space-y-1.5 sm:col-span-2">
            <span className="flex items-center gap-1 text-xs font-medium text-muted-foreground">
              <Calendar className="h-3.5 w-3.5" />
              Ngày sử dụng vé
            </span>
            <input
              type="date"
              value={visitDate}
              min={new Date().toISOString().slice(0, 10)}
              onChange={(e) => setVisitDate(e.target.value)}
              className="w-full rounded-xl border border-border bg-background px-3 py-2 text-sm"
            />
          </label>
        </div>

        {selectedSite && (
          <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
            <MapPin className="h-3.5 w-3.5" />
            {selectedSite.tag} · Mã booking: {selectedSite.code}
          </p>
        )}

        <button
          type="button"
          onClick={handleSearch}
          disabled={loadingPrices || !siteCode}
          className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-soft disabled:opacity-60"
        >
          {loadingPrices ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Search className="h-4 w-4" />
          )}
          {loadingPrices ? "Đang lấy giá..." : "Xem giá vé"}
        </button>
      </div>

      {priceError && (
        <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {priceError}
        </div>
      )}

      {prices && (
        <div className="space-y-3 animate-fade-in-up">
          <p className="text-xs text-muted-foreground">
            {prices.siteName ?? selectedSite?.name} · {prices.usingDate} ·{" "}
            {prices.tickets.length} mức giá
          </p>
          {prices.tickets.length === 0 ? (
            <p className="rounded-2xl border border-border bg-muted/40 p-4 text-sm text-muted-foreground">
              Không có vé khả dụng cho ngày này.
            </p>
          ) : (
            <ul className="space-y-2">
              {prices.tickets.map((t, i) => (
                <li
                  key={`${t.name}-${i}`}
                  className="flex items-start justify-between gap-3 rounded-2xl border border-border bg-card p-4"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-foreground">
                      {t.name}
                    </p>
                  </div>
                  <div className="shrink-0 text-right">
                    {t.originalPrice != null && t.originalPrice > t.salePrice && (
                      <p className="text-[11px] text-muted-foreground line-through">
                        {formatVnd(t.originalPrice)}
                      </p>
                    )}
                    <p className="text-sm font-bold tabular-nums text-primary">
                      {formatVnd(t.salePrice)}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
