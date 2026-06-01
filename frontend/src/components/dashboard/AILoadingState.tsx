/**
 * AI Loading State — adapted from kokonutui (MIT)
 * Driven by real agent trace lines from the backend.
 */

import { useEffect, useId, useRef, useState } from "react";

export type AgentProgress = {
  status: string;
  lines: string[];
  progress: number;
};

function LoadingAnimation({ progress }: { progress: number }) {
  const maskId = useId();
  return (
    <div className="relative h-6 w-6 shrink-0">
      <svg
        aria-label={`Tiến độ: ${Math.round(progress)}%`}
        className="h-full w-full"
        fill="none"
        viewBox="0 0 240 240"
        xmlns="http://www.w3.org/2000/svg"
      >
        <title>Tiến độ xử lý</title>
        <defs>
          <mask id={maskId}>
            <rect fill="black" height="240" width="240" />
            <circle
              cx="120"
              cy="120"
              fill="white"
              r="120"
              strokeDasharray={`${(progress / 100) * 754}, 754`}
              transform="rotate(-90 120 120)"
            />
          </mask>
        </defs>
        <style>
          {`
            @keyframes vw-rotate-cw { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
            @keyframes vw-rotate-ccw { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }
            .vw-g-spin circle { transform-origin: 120px 120px; }
            .vw-g-spin circle:nth-child(1) { animation: vw-rotate-cw 8s linear infinite; }
            .vw-g-spin circle:nth-child(2) { animation: vw-rotate-ccw 8s linear infinite; }
            .vw-g-spin circle:nth-child(3) { animation: vw-rotate-cw 8s linear infinite; }
            .vw-g-spin circle:nth-child(4) { animation: vw-rotate-ccw 8s linear infinite; }
            .vw-g-spin circle:nth-child(5) { animation: vw-rotate-cw 8s linear infinite; }
            .vw-g-spin circle:nth-child(6) { animation: vw-rotate-ccw 8s linear infinite; }
          `}
        </style>
        <g
          className="vw-g-spin"
          mask={`url(#${maskId})`}
          strokeDasharray="18% 40%"
          strokeWidth="16"
        >
          <circle cx="120" cy="120" opacity="0.95" r="150" stroke="#FF2E7E" />
          <circle cx="120" cy="120" opacity="0.95" r="130" stroke="#00E5FF" />
          <circle cx="120" cy="120" opacity="0.95" r="110" stroke="#4ADE80" />
          <circle cx="120" cy="120" opacity="0.95" r="90" stroke="#FFA726" />
          <circle cx="120" cy="120" opacity="0.95" r="70" stroke="#FFEB3B" />
          <circle cx="120" cy="120" opacity="0.95" r="50" stroke="#FF4081" />
        </g>
      </svg>
    </div>
  );
}

type Props = {
  progress: AgentProgress;
};

const LINE_HEIGHT = 28;
const VISIBLE_ROWS = 3;

export function AILoadingState({ progress }: Props) {
  const codeContainerRef = useRef<HTMLDivElement>(null);
  const [scrollPosition, setScrollPosition] = useState(0);

  const lines = progress.lines.length > 0 ? progress.lines : [progress.status];
  const visibleLines = lines.map((text, i) => ({ text, number: i + 1 }));

  useEffect(() => {
    const maxScroll = Math.max(0, (visibleLines.length - VISIBLE_ROWS) * LINE_HEIGHT);
    setScrollPosition(maxScroll);
  }, [visibleLines.length]);

  useEffect(() => {
    if (codeContainerRef.current) {
      codeContainerRef.current.scrollTop = scrollPosition;
    }
  }, [scrollPosition]);

  return (
    <div className="w-full min-w-[260px] space-y-3 py-1">
      <div className="flex items-center gap-2 font-medium text-muted-foreground">
        <LoadingAnimation progress={progress.progress} />
        <span className="text-sm text-foreground">{progress.status}</span>
      </div>

      <div className="relative rounded-lg border border-border/60 bg-muted/30">
        <div
          ref={codeContainerRef}
          className="relative h-[84px] overflow-hidden font-mono text-[11px]"
          style={{ scrollBehavior: "smooth" }}
        >
          <div>
            {visibleLines.map((line) => (
              <div
                key={`${line.number}-${line.text}`}
                className="flex h-[28px] items-center px-2"
              >
                <div className="w-6 shrink-0 select-none pr-2 text-right text-muted-foreground">
                  {line.number}
                </div>
                <div className="min-w-0 flex-1 truncate text-foreground/90">
                  {line.text}
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="pointer-events-none absolute inset-0 rounded-lg bg-gradient-to-b from-card/90 via-transparent to-card/40" />
      </div>
    </div>
  );
}
