import { useState } from "react";
import { Bell, BellOff, MapPin, Plane, Hotel, Sparkles, TreePine, Ticket, Droplets } from "lucide-react";
import { itinerary } from "@/lib/mock-data";

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  plane: Plane,
  hotel: Hotel,
  show: Sparkles,
  safari: TreePine,
  park: Ticket,
  fountain: Droplets,
};

export function ItineraryTimeline() {
  const [reminded, setReminded] = useState<Set<string>>(new Set(["1-0", "1-3"]));

  const toggle = (key: string) =>
    setReminded((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });

  return (
    <div className="space-y-8 p-1">
      {itinerary.map((day) => (
        <div key={day.day} className="animate-fade-in-up">
          <div className="mb-4 flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-primary text-sm font-bold text-primary-foreground shadow-glow">
              D{day.day}
            </div>
            <div>
              <h3 className="text-base font-semibold tracking-tight text-foreground">
                Ngày {day.day}
              </h3>
              <p className="text-xs text-muted-foreground">{day.label}</p>
            </div>
          </div>

          <ol className="relative space-y-3 border-l-2 border-dashed border-border pl-6 ml-5">
            {day.items.map((item, i) => {
              const Icon = iconMap[item.icon] ?? Sparkles;
              const key = `${day.day}-${i}`;
              const on = reminded.has(key);
              return (
                <li key={key} className="relative">
                  <span className="absolute -left-[33px] top-3 grid h-6 w-6 place-items-center rounded-full border-2 border-background bg-card shadow-soft">
                    <Icon className="h-3 w-3 text-primary" />
                  </span>
                  <div className="group rounded-2xl border border-border bg-card p-4 transition-all hover:border-primary/40 hover:shadow-elevated">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="rounded-md bg-ocean/10 px-1.5 py-0.5 text-[11px] font-semibold tabular-nums text-ocean">
                            {item.time}
                          </span>
                          <span className="text-[11px] text-muted-foreground">{item.duration}</span>
                        </div>
                        <h4 className="mt-1.5 truncate text-sm font-semibold text-foreground">
                          {item.title}
                        </h4>
                        <p className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
                          <MapPin className="h-3 w-3" />
                          {item.location}
                        </p>
                      </div>
                      <button
                        onClick={() => toggle(key)}
                        className={`inline-flex shrink-0 items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-medium transition-all ${
                          on
                            ? "border-primary bg-primary/10 text-primary"
                            : "border-border bg-background text-muted-foreground hover:border-primary/40 hover:text-primary"
                        }`}
                      >
                        {on ? <Bell className="h-3 w-3" /> : <BellOff className="h-3 w-3" />}
                        {on ? "Đã hẹn" : "Hẹn giờ"}
                      </button>
                    </div>
                  </div>
                </li>
              );
            })}
          </ol>
        </div>
      ))}
    </div>
  );
}
