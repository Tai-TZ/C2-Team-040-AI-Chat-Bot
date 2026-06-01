import { useEffect, useState } from "react";
import { subscribeOpenTicketsTab } from "@/lib/vinwonders-events";
import {
  IDLE_DASHBOARD,
  subscribeDashboardContext,
  type DashboardContext,
} from "@/lib/dashboard-context";
import { CalendarDays, Ticket, Sparkles } from "lucide-react";
import { ItineraryTimeline } from "./ItineraryTimeline";
import { TicketsFlights } from "./TicketsFlights";
import { LiveEvents } from "./LiveEvents";
import { DashboardContextPanel } from "./DashboardContextPanel";

const tabs = [
  { id: "context", label: "AI đang tư vấn", icon: Sparkles },
  { id: "itinerary", label: "Lịch trình", icon: CalendarDays },
  { id: "tickets", label: "Vé & Chuyến bay", icon: Ticket },
  { id: "events", label: "Sự kiện Live", icon: Sparkles },
] as const;

type TabId = (typeof tabs)[number]["id"];

export function Canvas() {
  const [tab, setTab] = useState<TabId>("context");
  const [dashboard, setDashboard] = useState<DashboardContext>(IDLE_DASHBOARD);

  useEffect(() => {
    return subscribeDashboardContext((ctx) => {
      setDashboard(ctx);
      if (ctx.focus !== "idle") {
        setTab("context");
      }
    });
  }, []);

  useEffect(() => {
    return subscribeOpenTicketsTab(() => setTab("tickets"));
  }, []);

  return (
    <div className="flex h-full flex-col bg-gradient-to-br from-background via-background to-accent/30">
      <div className="px-4 pt-4">
        <div className="inline-flex w-full flex-wrap gap-1 rounded-2xl border border-border bg-surface p-1 shadow-soft">
          {tabs.map((t) => {
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => setTab(t.id)}
                className={`relative inline-flex flex-1 items-center justify-center gap-1.5 rounded-xl px-2 py-2 text-[11px] font-semibold transition-all sm:flex-none sm:px-3 sm:text-xs ${
                  active
                    ? "bg-gradient-primary text-primary-foreground shadow-soft"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <t.icon className="h-3.5 w-3.5 shrink-0" />
                <span className="hidden sm:inline">{t.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-4">
        <div key={tab} className="animate-fade-in-up">
          {tab === "context" && <DashboardContextPanel ctx={dashboard} />}
          {tab === "itinerary" && <ItineraryTimeline />}
          {tab === "tickets" && <TicketsFlights />}
          {tab === "events" && <LiveEvents />}
        </div>
      </div>
    </div>
  );
}
