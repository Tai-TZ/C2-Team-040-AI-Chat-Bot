import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { MessageSquare, X } from "lucide-react";
import { ChatPanel } from "@/components/dashboard/ChatPanel";
import { Canvas } from "@/components/dashboard/Canvas";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "VinWonders Tour Guide · AI Travel Concierge" },
      { name: "description", content: "AI-powered travel planning for VinWonders Phú Quốc — itineraries, tickets, flights and live shows." },
      { property: "og:title", content: "VinWonders Tour Guide" },
      { property: "og:description", content: "Plan luxury VinWonders getaways in seconds with your AI concierge." },
    ],
  }),
  component: Index,
});

function Index() {
  const [chatOpen, setChatOpen] = useState(false);

  return (
    <div className="h-screen w-full overflow-hidden bg-background">
      <div className="flex h-full">
        {/* Chat — desktop */}
        <aside className="hidden md:flex md:w-[45%] lg:w-[42%] xl:w-[40%] border-r border-border">
          <ChatPanel />
        </aside>

        {/* Canvas */}
        <main className="flex-1 min-w-0">
          <Canvas />
        </main>
      </div>

      {/* Mobile chat FAB */}
      <button
        onClick={() => setChatOpen(true)}
        className="md:hidden fixed bottom-5 right-5 z-40 inline-flex items-center gap-2 rounded-full bg-gradient-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-glow active:scale-95"
        aria-label="Open chat"
      >
        <MessageSquare className="h-4 w-4" />
        Hỏi AI
      </button>

      {/* Mobile bottom sheet */}
      {chatOpen && (
        <div className="md:hidden fixed inset-0 z-50">
          <button
            onClick={() => setChatOpen(false)}
            className="absolute inset-0 bg-foreground/40 backdrop-blur-sm animate-fade-in-up"
            aria-label="Close"
          />
          <div className="absolute inset-x-0 bottom-0 top-12 overflow-hidden rounded-t-3xl bg-surface shadow-elevated animate-fade-in-up">
            <button
              onClick={() => setChatOpen(false)}
              className="absolute right-4 top-4 z-10 grid h-9 w-9 place-items-center rounded-full bg-muted text-muted-foreground"
              aria-label="Close chat"
            >
              <X className="h-4 w-4" />
            </button>
            <ChatPanel />
          </div>
        </div>
      )}
    </div>
  );
}
