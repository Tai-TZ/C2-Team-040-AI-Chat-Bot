import { MapPin, Sparkles, Ticket } from "lucide-react";
import type { DashboardContext } from "@/lib/dashboard-context";
import type { PriceQuote } from "@/lib/chat-types";
import { WeatherCard } from "./WeatherCard";
import { VinWondersPrices } from "./VinWondersPrices";

type Props = {
  ctx: DashboardContext;
};

function PriceSummary({ quote }: { quote: PriceQuote }) {
  return (
    <div className="rounded-2xl border border-border bg-card p-4 shadow-soft">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold">
        <Ticket className="h-4 w-4 text-primary" />
        Giá vé · {quote.siteName}
      </h3>
      <p className="mb-3 text-xs text-muted-foreground">
        Ngày {quote.usingDate}
        {quote.cheapestFormatted && (
          <>
            {" "}
            · Từ{" "}
            <span className="font-bold text-primary">{quote.cheapestFormatted}</span>
          </>
        )}
      </p>
      <ul className="max-h-48 space-y-2 overflow-y-auto scrollbar-thin">
        {quote.tickets.slice(0, 5).map((t) => (
          <li
            key={`${t.name}-${t.salePrice}`}
            className={`flex justify-between gap-2 rounded-xl border px-3 py-2 text-xs ${
              t.isCheapest ? "border-primary/40 bg-primary/5" : "border-border"
            }`}
          >
            <span className="line-clamp-2 text-foreground">{t.name}</span>
            <span className="shrink-0 font-bold text-primary">
              {t.salePriceFormatted}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function DashboardContextPanel({ ctx }: Props) {
  const dest = ctx.destination;
  const title =
    dest?.siteName || dest?.region || "VinWonders Tour Guide";
  const subtitle = dest?.usingDate
    ? `${dest.region ? `${dest.region} · ` : ""}Ngày ${dest.usingDate}`
    : "Chọn địa điểm và ngày trong chat để xem chi tiết";

  const focusLabel =
    ctx.focus === "weather"
      ? "Đang xem: Thời tiết"
      : ctx.focus === "prices"
        ? "Đang xem: Giá vé"
        : "Hành trình gợi ý";

  return (
    <div className="space-y-4 animate-fade-in-up">
      <div className="rounded-2xl border border-primary/20 bg-gradient-to-r from-primary/10 to-accent/30 p-4">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-primary">
          <Sparkles className="h-3 w-3" />
          {focusLabel}
        </span>
        <h2 className="mt-2 text-xl font-bold text-foreground">{title}</h2>
        <p className="mt-1 flex items-center gap-1.5 text-sm text-muted-foreground">
          <MapPin className="h-3.5 w-3.5" />
          {subtitle}
        </p>
      </div>

      {ctx.weather && (
        <WeatherCard
          weather={ctx.weather}
          compact={ctx.focus === "prices"}
        />
      )}

      {ctx.focus === "prices" && ctx.priceQuote && (
        <PriceSummary quote={ctx.priceQuote} />
      )}

      {ctx.focus === "prices" && (
        <div className="rounded-2xl border border-dashed border-border bg-muted/20 p-3">
          <p className="mb-2 text-xs font-medium text-muted-foreground">
            Tra cứu thêm trên bảng giá
          </p>
          <VinWondersPrices />
        </div>
      )}

      {ctx.focus === "idle" && (
        <p className="rounded-2xl border border-border bg-card/50 p-6 text-center text-sm text-muted-foreground">
          Hỏi AI về điểm đến và ngày đi — bảng bên phải sẽ hiển thị thời tiết và giá vé
          song song với chat.
        </p>
      )}
    </div>
  );
}
