/** 日時の表示用フォーマット。API の日時は UTC の ISO 文字列で、表示はブラウザのローカル時刻。 */

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
  if (isSameDay(date, now)) return formatTime(iso);
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (isSameDay(date, yesterday)) return "昨日";
  return shortDateFormatter.format(date);
}

/** 2 つの日時がローカル時刻で同じ日か */
export function isSameDay(a: Date | string, b: Date | string): boolean {
  return new Date(a).toDateString() === new Date(b).toDateString();
}
