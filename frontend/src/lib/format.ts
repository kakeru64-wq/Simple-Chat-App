import type { Message } from "./types";

const timeFormatter = new Intl.DateTimeFormat("ja-JP", { hour: "2-digit", minute: "2-digit" });
const dateFormatter = new Intl.DateTimeFormat("ja-JP", {
  year: "numeric",
  month: "numeric",
  day: "numeric",
  weekday: "short",
});

/** "14:05" */
export function formatTime(iso: string): string {
  return timeFormatter.format(new Date(iso));
}

/** "2026/11/14(土)" */
export function formatDate(iso: string): string {
  return dateFormatter.format(new Date(iso));
}

/** 日付区切りを表示すべきか（ローカル日付が前のメッセージと異なるか） */
export function isNewDay(prev: Message | undefined, current: Message): boolean {
  if (!prev) return true;
  return new Date(prev.created_at).toDateString() !== new Date(current.created_at).toDateString();
}

/** id で重複を除き、古い順に並べる（REST と WebSocket の両方から届くため） */
export function mergeMessages(current: Message[], incoming: Message[]): Message[] {
  const byId = new Map(current.map((m) => [m.id, m]));
  for (const m of incoming) byId.set(m.id, m);
  return [...byId.values()].sort((a, b) => a.id - b.id);
}
