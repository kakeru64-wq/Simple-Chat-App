import type { Message } from "./types";

const timeFormatter = new Intl.DateTimeFormat("ja-JP", { hour: "2-digit", minute: "2-digit" });
const dateFormatter = new Intl.DateTimeFormat("ja-JP", {
  year: "numeric",
  month: "numeric",
  day: "numeric",
  weekday: "short",
});
const shortDateFormatter = new Intl.DateTimeFormat("ja-JP", { month: "numeric", day: "numeric" });

/** "14:05" */
export function formatTime(iso: string): string {
  return timeFormatter.format(new Date(iso));
}

/** "2026/11/14(土)" */
export function formatDate(iso: string): string {
  return dateFormatter.format(new Date(iso));
}

/** トーク一覧用：今日なら時刻、昨日なら「昨日」、それ以前は "11/12" */
export function formatListTime(iso: string, now: Date = new Date()): string {
  const date = new Date(iso);
  if (date.toDateString() === now.toDateString()) return formatTime(iso);
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (date.toDateString() === yesterday.toDateString()) return "昨日";
  return shortDateFormatter.format(date);
}

/** トーク一覧に表示する最新メッセージのプレビュー */
export function previewText(message: Message, myUserId: number): string {
  const sender = message.user.id === myUserId ? "あなた" : message.user.name;
  if (message.is_deleted) return `${sender}がメッセージの送信を取り消しました`;
  if (message.image_url) return `${sender}が画像を送信しました`;
  return `${sender}: ${message.content ?? ""}`;
}

/** 未読バッジの表示（多すぎる場合は省略） */
export function formatUnread(count: number): string {
  return count > 99 ? "99+" : String(count);
}

/** 日付区切りを表示すべきか（ローカル日付が前のメッセージと異なるか） */
export function isNewDay(prev: Message | undefined, current: Message): boolean {
  if (!prev) return true;
  return new Date(prev.created_at).toDateString() !== new Date(current.created_at).toDateString();
}

/**
 * id で重複を除き、古い順に並べる。
 * REST と WebSocket の両方から同じメッセージが届くため。同じ id は新しい方（削除反映など）で上書きする。
 */
export function mergeMessages(current: Message[], incoming: Message[]): Message[] {
  const byId = new Map(current.map((m) => [m.id, m]));
  for (const m of incoming) byId.set(m.id, m);
  return [...byId.values()].sort((a, b) => a.id - b.id);
}
