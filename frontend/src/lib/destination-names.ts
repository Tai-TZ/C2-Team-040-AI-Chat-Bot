/**
 * Labels aligned with vinwonders_destinations_data.json (destination_name).
 * Extra patterns cover common aliases in user messages.
 */
export const VINWONDERS_DESTINATION_MATCHERS: {
  label: string;
  patterns: RegExp[];
}[] = [
  { label: "Nha Trang", patterns: [/nha\s*trang/i] },
  { label: "Phú Quốc", patterns: [/ph[uú]\s*qu[oố]c/i, /phu\s*quoc/i] },
  { label: "Hà Nội", patterns: [/hà\s*nội/i, /ha\s*noi/i, /\bhanoi\b/i] },
  {
    label: "Nghệ An - Hà Tĩnh",
    patterns: [/nghệ\s*an/i, /nghe\s*an/i, /hà\s*tĩnh/i, /ha\s*tinh/i],
  },
  {
    label: "Đà Nẵng - Hội An",
    patterns: [/đà\s*nẵng/i, /da\s*nang/i, /hội\s*an/i, /hoi\s*an/i],
  },
  { label: "Hải Phòng", patterns: [/hải\s*phòng/i, /hai\s*phong/i] },
  {
    label: "Thành Phố Hồ Chí Minh",
    patterns: [
      /tp\.?\s*hồ\s*chí\s*minh/i,
      /hồ\s*chí\s*minh/i,
      /ho\s*chi\s*minh/i,
      /\bsài\s*gòn\b/i,
      /\bsai\s*gon\b/i,
      /\btphcm\b/i,
    ],
  },
];

export function matchDestinationInText(text: string): string {
  const q = text.trim();
  if (!q) return "điểm đến của bạn";
  for (const { label, patterns } of VINWONDERS_DESTINATION_MATCHERS) {
    if (patterns.some((p) => p.test(q))) return label;
  }
  return "điểm đến của bạn";
}
