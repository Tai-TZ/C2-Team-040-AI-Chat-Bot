import { Plane, ArrowRight } from "lucide-react";
import { flights, formatVND } from "@/lib/mock-data";
import { VinWondersPrices } from "./VinWondersPrices";

export function TicketsFlights() {
  return (
    <div className="space-y-6 p-1">
      <VinWondersPrices />

      <section>
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
          <Plane className="h-4 w-4 text-primary" /> Chuyến bay đề xuất
        </h3>
        <p className="mb-3 text-xs text-muted-foreground">
          Gợi ý chuyến bay mẫu — có thể thay bằng API hãng sau.
        </p>
        <div className="space-y-3">
          {flights.map((f) => (
            <FlightCard key={f.id} f={f} />
          ))}
        </div>
      </section>
    </div>
  );
}

function FlightCard({ f }: { f: (typeof flights)[number] }) {
  return (
    <div className="group rounded-2xl border border-border bg-card p-4 transition-all hover:border-primary/40 hover:shadow-elevated animate-fade-in-up">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-ocean/10 text-ocean">
            <Plane className="h-4 w-4" />
          </div>
          <div>
            <p className="text-xs font-semibold text-foreground">{f.airline}</p>
            <p className="text-[11px] text-muted-foreground">
              {f.code} · {f.date}
            </p>
          </div>
        </div>
        <span className="rounded-full bg-success/10 px-2 py-0.5 text-[11px] font-medium text-success">
          {f.stops}
        </span>
      </div>

      <div className="flex items-center justify-between gap-3">
        <div className="text-center">
          <p className="text-lg font-bold tabular-nums text-foreground">
            {f.from.time}
          </p>
          <p className="text-[11px] text-muted-foreground">{f.from.code}</p>
        </div>

        <div className="flex-1">
          <div className="relative h-px bg-border">
            <div className="absolute inset-0 bg-gradient-to-r from-primary/0 via-primary to-primary/0" />
            <Plane className="absolute left-1/2 top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rotate-90 text-primary" />
          </div>
          <p className="mt-2 text-center text-[11px] text-muted-foreground">
            {f.duration}
          </p>
        </div>

        <div className="text-center">
          <p className="text-lg font-bold tabular-nums text-foreground">
            {f.to.time}
          </p>
          <p className="text-[11px] text-muted-foreground">{f.to.code}</p>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-dashed border-border pt-3">
        <div>
          <p className="text-[11px] text-muted-foreground">Từ</p>
          <p className="text-sm font-bold text-foreground">
            {formatVND(f.price)}
          </p>
        </div>
        <button
          type="button"
          className="inline-flex items-center gap-1.5 rounded-xl bg-foreground px-3.5 py-2 text-xs font-semibold text-background transition-transform hover:scale-105 active:scale-95"
        >
          Đặt vé <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
