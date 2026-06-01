import { useEffect, useState } from "react";
import { subscribeOpenTicketsTab } from "@/lib/vinwonders-events";
import { CalendarDays, Ticket, Sparkles, MapPin, Users, Clock } from "lucide-react";
import { ItineraryTimeline } from "./ItineraryTimeline";
import { TicketsFlights } from "./TicketsFlights";
import { LiveEvents } from "./LiveEvents";
import heroImg from "@/assets/vinwonders-hero.jpg";

const tabs = [
  { id: "itinerary", label: "Lịch trình", icon: CalendarDays },
  { id: "tickets", label: "Vé & Chuyến bay", icon: Ticket },
  { id: "events", label: "Sự kiện Live", icon: Sparkles },
] as const;

type TabId = (typeof tabs)[number]["id"];

export function Canvas() {
  const [tab, setTab] = useState<TabId>("tickets");

  useEffect(() => {
    return subscribeOpenTicketsTab(() => setTab("tickets"));
  }, []);

  return (
    <div className="flex h-full flex-col bg-gradient-to-br from-background via-background to-accent/30">
      {/* Hero summary */}
      <div className="relative m-4 mb-0 overflow-hidden rounded-3xl shadow-elevated">
        <img
          src={heroImg}
          alt="VinWonders Phú Quốc"
          width={1280}
          height={800}
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-tr from-ocean/90 via-ocean/60 to-primary/40" />
        <div className="relative p-6 text-ocean-foreground">
          <span className="inline-flex items-center gap-1.5 rounded-full glass-strong px-2.5 py-1 text-[11px] font-semibold text-white">
            <Sparkles className="h-3 w-3" />
            Hành trình do AI thiết kế
          </span>
          <h2 className="mt-3 text-2xl font-bold tracking-tight md:text-3xl">
            Phú Quốc · 2 ngày 1 đêm
          </h2>
          <p className="mt-1 text-sm text-white/80">
            Hà Nội → Phú Quốc · 07–08/06 · Vinpearl Resort & VinWonders
          </p>
          <div className="mt-4 flex flex-wrap gap-4 text-xs text-white/90">
            <span className="inline-flex items-center gap-1.5"><MapPin className="h-3.5 w-3.5" />5 điểm đến</span>
            <span className="inline-flex items-center gap-1.5"><Clock className="h-3.5 w-3.5" />48 giờ</span>
            <span className="inline-flex items-center gap-1.5"><Users className="h-3.5 w-3.5" />2 khách</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="px-4 pt-4">
        <div className="inline-flex w-full rounded-2xl border border-border bg-surface p-1 shadow-soft md:w-auto">
          {tabs.map((t) => {
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`relative inline-flex flex-1 items-center justify-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold transition-all md:flex-none md:px-4 ${
                  active
                    ? "bg-gradient-primary text-primary-foreground shadow-soft"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <t.icon className="h-3.5 w-3.5" />
                {t.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin p-4">
        <div key={tab} className="animate-fade-in-up">
          {tab === "itinerary" && <ItineraryTimeline />}
          {tab === "tickets" && <TicketsFlights />}
          {tab === "events" && <LiveEvents />}
        </div>
      </div>
    </div>
  );
}
