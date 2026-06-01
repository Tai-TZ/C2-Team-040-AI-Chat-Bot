import { ExternalLink, MapPin } from "lucide-react";
import type { DestinationMap } from "@/lib/chat-types";

type Props = {
  map: DestinationMap;
  compact?: boolean;
};

export function VinWondersMapEmbed({ map, compact }: Props) {
  const height = compact ? 200 : 260;

  return (
    <div className="mt-3 overflow-hidden rounded-xl border border-border/70 bg-muted/20">
      <div className="flex items-center justify-between gap-2 border-b border-border/60 bg-background/80 px-3 py-2">
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
            <MapPin className="h-3.5 w-3.5 shrink-0 text-primary" />
            Bản đồ VinWonders — {map.region}
          </p>
          <p className="text-[10px] text-muted-foreground">
            {map.subLocationCount} điểm trải nghiệm · dữ liệu nội bộ
          </p>
        </div>
        <a
          href={`https://www.openstreetmap.org/?mlat=${map.center.lat}&mlon=${map.center.lng}#map=${map.zoom}/${map.center.lat}/${map.center.lng}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex shrink-0 items-center gap-1 rounded-full border border-border px-2 py-1 text-[10px] font-medium text-muted-foreground transition-colors hover:border-primary/40 hover:text-primary"
        >
          <ExternalLink className="h-3 w-3" />
          Mở OSM
        </a>
      </div>

      <iframe
        title={`Bản đồ VinWonders ${map.region}`}
        src={map.embedUrl}
        className="w-full border-0 bg-muted"
        style={{ height }}
        loading="lazy"
        referrerPolicy="no-referrer-when-downgrade"
      />

      {map.markers.length > 0 && (
        <ul className="max-h-32 space-y-1 overflow-y-auto border-t border-border/60 bg-background/60 px-3 py-2 scrollbar-thin">
          {map.markers.map((m) => (
            <li
              key={m.code}
              className="flex items-start gap-2 text-[11px] leading-snug text-foreground/90"
            >
              <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
              <span className="min-w-0 flex-1">
                <span className="font-medium">{m.name}</span>
                {m.tag ? (
                  <span className="text-muted-foreground"> · {m.tag}</span>
                ) : null}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
