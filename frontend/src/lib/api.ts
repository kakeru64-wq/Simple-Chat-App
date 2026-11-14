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
  method?: "GET" | "POST";
  body?: unknown;
  /** false の場合は Authorization ヘッダーを付けない（ログイン時） */
  auth?: boolean;
};

async function request<T>(path: string, { method = "GET", body, auth = true }: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getSession()?.token;
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "サーバーに接続できませんでした");
  }

  if (res.status === 401 && auth) {
    // トークン失効：ログイン情報を消すと、各画面のガードがログイン画面へ戻す
    clearSession();
  }
  if (!res.ok) {
    throw new ApiError(res.status, await extractErrorMessage(res));
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

async function extractErrorMessage(res: Response): Promise<string> {
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

export const api = {
  login: (name: string) =>
    request<LoginResponse>("/api/auth/login", { method: "POST", body: { name }, auth: false }),
  me: () => request<User>("/api/auth/me"),
  logout: () => request<void>("/api/auth/logout", { method: "POST" }),

  listRooms: () => request<Room[]>("/api/rooms"),
  getRoom: (roomId: number) => request<Room>(`/api/rooms/${roomId}`),
  createRoom: (name: string) => request<Room>("/api/rooms", { method: "POST", body: { name } }),

  listMessages: (roomId: number, beforeId?: number) => {
    const params = new URLSearchParams({ limit: String(MESSAGE_PAGE_SIZE) });
    if (beforeId !== undefined) params.set("before_id", String(beforeId));
    return request<MessageListResponse>(`/api/rooms/${roomId}/messages?${params}`);
  },
  postMessage: (roomId: number, content: string) =>
    request<Message>(`/api/rooms/${roomId}/messages`, { method: "POST", body: { content } }),
};
