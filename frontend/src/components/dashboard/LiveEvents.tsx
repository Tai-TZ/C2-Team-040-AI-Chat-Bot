import { Star, MapPin, Radio } from "lucide-react";
import { events } from "@/lib/mock-data";

const statusStyles: Record<string, { dot: string; label: string; pulse: boolean }> = {
  live: { dot: "bg-destructive", label: "LIVE", pulse: true },
  soon: { dot: "bg-primary", label: "SẮP DIỄN RA", pulse: true },
  scheduled: { dot: "bg-muted-foreground", label: "LỊCH CHIẾU", pulse: false },
};

export function LiveEvents() {
  return (
    <div className="grid gap-4 p-1 sm:grid-cols-2 lg:grid-cols-3">
      {events.map((e, i) => {
        const s = statusStyles[e.status];
        return (
          <div
            key={e.id}
            className="group relative overflow-hidden rounded-2xl border border-border bg-card transition-all hover:shadow-elevated animate-fade-in-up"
            style={{ animationDelay: `${i * 60}ms` }}
          >
            <div className="relative aspect-[4/5] overflow-hidden">
              <img
                src={e.image}
                alt={e.title}
                loading="lazy"
                className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/30 to-transparent" />

              <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-full glass-strong px-2.5 py-1">
                <span
                  className={`relative h-1.5 w-1.5 rounded-full ${s.dot} ${
                    s.pulse ? "animate-pulse-ring" : ""
                  }`}
                />
                <span className="text-[10px] font-bold tracking-wider text-white">{s.label}</span>
              </div>

              <div className="absolute right-3 top-3 flex items-center gap-1 rounded-full glass-strong px-2 py-1">
                <Star className="h-3 w-3 fill-primary text-primary" />
                <span className="text-[11px] font-semibold text-white tabular-nums">{e.rating}</span>
              </div>

              <div className="absolute bottom-0 left-0 right-0 p-4 text-white">
                <h4 className="text-base font-bold leading-tight">{e.title}</h4>
                <p className="mt-1 flex items-center gap-1 text-[11px] text-white/80">
                  <MapPin className="h-3 w-3" /> {e.venue}
                </p>
                <div className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-white/15 backdrop-blur px-2.5 py-1 text-[11px] font-medium text-white">
                  <Radio className="h-3 w-3" />
                  {e.countdown}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
