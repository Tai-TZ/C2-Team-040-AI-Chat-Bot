import { ExternalLink, MessageCircle, Sparkles, Ticket } from "lucide-react";
import { getAssistantActions } from "@/lib/chat-actions";
import { MessageAgentTrace } from "./MessageAgentTrace";
import { renderChatText } from "@/lib/format-chat-text";
import type { ChatAction, ChatMessage, PriceQuote } from "@/lib/chat-types";
import { dispatchOpenTicketsTab } from "@/lib/vinwonders-events";
import { VinWondersMapEmbed } from "./VinWondersMapEmbed";
import { WeatherCard } from "./WeatherCard";

type Props = {
  message: ChatMessage;
  onAction: (action: ChatAction) => void;
};

function PriceCards({ quote }: { quote: PriceQuote }) {
  return (
    <div className="mt-3 space-y-2">
      <div className="flex items-center justify-between gap-2 rounded-xl bg-primary/5 px-3 py-2">
        <div className="min-w-0">
          <p className="text-xs font-medium text-primary">
            {quote.siteName || quote.region}
          </p>
          <p className="text-[11px] text-muted-foreground">
            Ngày {quote.usingDate}
            {quote.cheapestFormatted && (
              <>
                {" "}
                · Rẻ nhất{" "}
                <span className="font-semibold text-foreground">
                  {quote.cheapestFormatted}
                </span>
              </>
            )}
          </p>
        </div>
        <Ticket className="h-4 w-4 shrink-0 text-primary" />
      </div>

      <ul className="space-y-2">
        {quote.tickets.map((t) => (
          <li
            key={`${t.name}-${t.salePrice}`}
            className={`rounded-xl border px-3 py-2.5 transition-colors ${
              t.isCheapest
                ? "border-primary/40 bg-primary/5 shadow-soft"
                : "border-border bg-background/80"
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-xs leading-snug text-foreground line-clamp-2">
                {t.isCheapest && (
                  <span className="mr-1.5 inline-flex rounded-full bg-primary px-1.5 py-0.5 text-[10px] font-semibold text-primary-foreground">
                    Rẻ nhất
                  </span>
                )}
                {t.name}
              </p>
              <div className="shrink-0 text-right">
                <p className="text-sm font-bold text-primary">
                  {t.salePriceFormatted}
                </p>
                {t.originalPriceFormatted &&
                  t.originalPrice &&
                  t.originalPrice > t.salePrice && (
                    <p className="text-[10px] text-muted-foreground line-through">
                      {t.originalPriceFormatted}
                    </p>
                  )}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ActionButtons({
  actions,
  onAction,
}: {
  actions: ChatAction[];
  onAction: (action: ChatAction) => void;
}) {
  return (
    <div className="mt-4 border-t border-border/60 pt-3">
      <p className="mb-2 flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
        <MessageCircle className="h-3.5 w-3.5 text-primary" />
        Bạn muốn làm gì tiếp theo?
      </p>
      <div className="flex flex-wrap gap-2">
      {actions.map((action) => {
        if (action.kind === "link") {
          return (
            <a
              key={action.id}
              href={action.href}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-full bg-gradient-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground shadow-soft transition-transform hover:scale-[1.02] active:scale-95"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              {action.label}
            </a>
          );
        }

        const variant =
          action.kind === "tab"
            ? "border-primary/50 bg-primary/5 text-primary hover:bg-primary/10"
            : "border-border bg-background text-foreground hover:border-primary/40 hover:bg-accent";

        return (
          <button
            key={action.id}
            type="button"
            onClick={() => onAction(action)}
            className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-all active:scale-95 ${variant}`}
          >
            {action.kind === "tab" && <Ticket className="h-3.5 w-3.5" />}
            {action.label}
          </button>
        );
      })}
      </div>
    </div>
  );
}

export function AssistantMessage({ message, onAction }: Props) {
  const quote = message.structured?.priceQuote;
  const weather = message.structured?.weather;
  const destinationMap = message.structured?.destinationMap;
  const actions = getAssistantActions(message);
  const showActions = actions.length > 0 && Boolean(message.content.trim());

  const handleAction = (action: ChatAction) => {
    if (action.kind === "tab") {
      dispatchOpenTicketsTab({
        supplierCode: action.supplierCode,
        usingDate: action.usingDate,
      });
      return;
    }
    onAction(action);
  };

  return (
    <div className="space-y-1">
      {weather && (
        <div className="mb-2">
          <WeatherCard weather={weather} compact />
        </div>
      )}

      {quote && (
        <div className="mb-2 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          <Sparkles className="h-3 w-3 text-primary" />
          Giá vé tra cứu trực tiếp
        </div>
      )}

      {quote && <PriceCards quote={quote} />}

      {message.content ? (
        <div className="whitespace-pre-wrap text-sm leading-relaxed">
          {renderChatText(message.content)}
        </div>
      ) : null}

      {destinationMap && (
        <VinWondersMapEmbed map={destinationMap} compact />
      )}

      {message.agentRun && (
        <MessageAgentTrace
          steps={message.agentRun.steps}
          toolCount={message.agentRun.toolCount}
        />
      )}

      {showActions && (
        <ActionButtons actions={actions} onAction={handleAction} />
      )}
    </div>
  );
}
