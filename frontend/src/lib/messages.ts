/** メッセージに関する純粋な関数（表示文の組み立て・並べ替え）。 */

import type { Message } from "./types";

/** ユーザーの投稿か（false ならシステムメッセージ） */
export function isUserMessage(message: Message): boolean {
  return message.kind === "text" || message.kind === "image";
}

/** 操作した人の表示名。自分なら「あなた」 */
function actorName(message: Message, myUserId: number): string {
  return message.user.id === myUserId ? "あなた" : message.user.name;
}

/**
 * 中央の帯に出す通知文（システムメッセージ・取り消し済み）。
 * 通常の吹き出しで表示するメッセージなら null。
 */
export function noticeText(message: Message, myUserId: number): string | null {
  const actor = actorName(message, myUserId);
  switch (message.kind) {
    case "room_renamed":
      return `${actor}がトーク名を「${message.content ?? ""}」に変更しました`;
    case "member_joined":
      return `${actor}が参加しました`;
    case "member_left":
      return `${actor}が退会しました`;
    default:
      return message.is_deleted ? `${actor}がメッセージの送信を取り消しました` : null;
  }
}

/** トーク一覧に出す、最新メッセージの 1 行プレビュー */
export function previewText(message: Message, myUserId: number): string {
  const notice = noticeText(message, myUserId);
  if (notice) return notice;
  const sender = actorName(message, myUserId);
  if (message.kind === "image") return `${sender}が画像を送信しました`;
  return `${sender}: ${message.content ?? ""}`;
}

/**
 * id で重複を除き、古い順に並べる。
 * REST と WebSocket の両方から同じメッセージが届くため。同じ id は後から来た方（取り消し反映など）で上書きする。
 */
export function mergeMessages(current: Message[], incoming: Message[]): Message[] {
  const byId = new Map(current.map((m) => [m.id, m]));
  for (const m of incoming) byId.set(m.id, m);
  return [...byId.values()].sort((a, b) => a.id - b.id);
}
