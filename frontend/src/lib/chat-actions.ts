import type { ChatAction, ChatMessage } from "./chat-types";

/** Shown under assistant replies when backend sends no actions yet. */
export const DEFAULT_FOLLOWUP_ACTIONS: ChatAction[] = [
  {
    id: "explore-nt",
    label: "Nha Trang cuối tuần sau",
    kind: "message",
    text: "Mình muốn đi Nha Trang cuối tuần sau, check thời tiết và giá vé",
  },
  {
    id: "explore-hn",
    label: "Hà Nội ngày mai",
    kind: "message",
    text: "Xem thời tiết và giá VinWonders Hà Nội ngày mai",
  },
  {
    id: "explore-pq",
    label: "Phú Quốc tuần sau",
    kind: "message",
    text: "Cho mình xem Phú Quốc tuần sau — thời tiết và giá vé",
  },
  {
    id: "other-dest",
    label: "Điểm đến khác",
    kind: "message",
    text: "Liệt kê các điểm VinWonders và gợi ý ngày đẹp để đi",
  },
];

export function getAssistantActions(message: ChatMessage): ChatAction[] {
  const fromServer = message.structured?.actions ?? [];
  if (fromServer.length > 0) {
    return fromServer;
  }
  if (message.role === "assistant" && message.content.trim()) {
    return DEFAULT_FOLLOWUP_ACTIONS;
  }
  return [];
}
