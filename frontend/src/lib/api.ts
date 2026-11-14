import { API_BASE_URL, MESSAGE_PAGE_SIZE } from "./config";
import { clearSession, getSession } from "./session";
import type { LoginResponse, Message, MessageListResponse, Room, User } from "./types";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  /** JSON にシリアライズするオブジェクト、または multipart 用の FormData */
  body?: unknown;
  /** false の場合は Authorization ヘッダーを付けない（ログイン時） */
  auth?: boolean;
};

async function request<T>(
  path: string,
  { method = "GET", body, auth = true }: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {};
  const isForm = body instanceof FormData;
  // FormData の場合は boundary 付きの Content-Type をブラウザに設定させる
  if (body !== undefined && !isForm) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getSession()?.token;
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "サーバーに接続できませんでした");
  }

  if (res.status === 401 && auth) {
    // トークン失効：ログイン情報を消すと、ログイン必須画面のガードがログイン画面へ戻す
    clearSession();
  }
  if (!res.ok) {
    throw new ApiError(res.status, await extractErrorMessage(res));
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

const STATUS_MESSAGES: Record<number, string> = {
  403: "この操作を行う権限がありません",
  404: "見つかりませんでした",
  413: "ファイルサイズが大きすぎます（5MBまで）",
  415: "対応していないファイル形式です（JPEG / PNG / GIF / WebP）",
};

async function extractErrorMessage(res: Response): Promise<string> {
  if (STATUS_MESSAGES[res.status]) return STATUS_MESSAGES[res.status];
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    // FastAPI のバリデーションエラーは配列で返る
    if (Array.isArray(data.detail) && data.detail[0]?.msg) return data.detail[0].msg;
  } catch {
    // JSON でないレスポンス
  }
  return `エラーが発生しました (${res.status})`;
}

/** API が返す相対パス（/uploads/...）をブラウザで開ける URL にする */
export function resolveMediaUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

export const api = {
  login: (name: string) =>
    request<LoginResponse>("/api/auth/login", { method: "POST", body: { name }, auth: false }),
  me: () => request<User>("/api/auth/me"),
  logout: () => request<void>("/api/auth/logout", { method: "POST" }),

  /** query を指定するとルーム名で部分一致検索する */
  listRooms: (query?: string) =>
    request<Room[]>(query ? `/api/rooms?${new URLSearchParams({ q: query })}` : "/api/rooms"),
  getRoom: (roomId: number) => request<Room>(`/api/rooms/${roomId}`),
  createRoom: (name: string) => request<Room>("/api/rooms", { method: "POST", body: { name } }),
  renameRoom: (roomId: number, name: string) =>
    request<Room>(`/api/rooms/${roomId}`, { method: "PATCH", body: { name } }),
  joinRoom: (roomId: number) => request<Room>(`/api/rooms/${roomId}/members/me`, { method: "PUT" }),
  leaveRoom: (roomId: number) =>
    request<void>(`/api/rooms/${roomId}/members/me`, { method: "DELETE" }),
  markRead: (roomId: number, messageId: number) =>
    request<void>(`/api/rooms/${roomId}/read`, {
      method: "PUT",
      body: { message_id: messageId },
    }),

  listMessages: (roomId: number, beforeId?: number) => {
    const params = new URLSearchParams({ limit: String(MESSAGE_PAGE_SIZE) });
    if (beforeId !== undefined) params.set("before_id", String(beforeId));
    return request<MessageListResponse>(`/api/rooms/${roomId}/messages?${params}`);
  },
  postMessage: (roomId: number, content: string) =>
    request<Message>(`/api/rooms/${roomId}/messages`, { method: "POST", body: { content } }),
  postImage: (roomId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<Message>(`/api/rooms/${roomId}/messages/images`, {
      method: "POST",
      body: form,
    });
  },
  deleteMessage: (roomId: number, messageId: number) =>
    request<Message>(`/api/rooms/${roomId}/messages/${messageId}`, { method: "DELETE" }),
};
