/** バックエンドの URL。`.env.local` の NEXT_PUBLIC_API_BASE_URL で上書きできる。 */
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

/** WebSocket の URL は API の URL から導出する（http → ws, https → wss）。 */
export const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");

/** 1 回の取得で読み込むメッセージ件数 */
export const MESSAGE_PAGE_SIZE = 50;

/** 入力値の上限（バックエンドのバリデーションと一致させる） */
export const LIMITS = {
  userName: 20,
  roomName: 30,
  message: 1000,
} as const;
