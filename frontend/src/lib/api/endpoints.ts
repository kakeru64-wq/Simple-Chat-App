import { MESSAGE_PAGE_SIZE } from "@/lib/config";
import type { LoginResponse, Message, MessageListResponse, Room, User } from "@/lib/types";

import { request } from "./client";

/** バックエンド API の一覧（backend/app/api/routes と 1 対 1 で対応） */
export const api = {
  // ---- 認証 /api/auth ----
  login: (name: string) =>
    request<LoginResponse>("/api/auth/login", { method: "POST", body: { name }, auth: false }),
  me: () => request<User>("/api/auth/me"),
  logout: () => request<void>("/api/auth/logout", { method: "POST" }),

  // ---- ルーム /api/rooms ----
  /** query を指定するとルーム名で部分一致検索する */
  listRooms: (query?: string) =>
    request<Room[]>(query ? `/api/rooms?${new URLSearchParams({ q: query })}` : "/api/rooms"),
  getRoom: (roomId: number) => request<Room>(`/api/rooms/${roomId}`),
  createRoom: (name: string) => request<Room>("/api/rooms", { method: "POST", body: { name } }),
  renameRoom: (roomId: number, name: string) =>
    request<Room>(`/api/rooms/${roomId}`, { method: "PATCH", body: { name } }),

  // ---- 参加・退会・既読 /api/rooms/{id}/members/me, /read ----
  joinRoom: (roomId: number) => request<Room>(`/api/rooms/${roomId}/members/me`, { method: "PUT" }),
  leaveRoom: (roomId: number) =>
    request<void>(`/api/rooms/${roomId}/members/me`, { method: "DELETE" }),
  markRead: (roomId: number, messageId: number) =>
    request<void>(`/api/rooms/${roomId}/read`, { method: "PUT", body: { message_id: messageId } }),

  // ---- メッセージ /api/rooms/{id}/messages ----
  /** beforeId を指定すると、それより古いメッセージを取得する（過去ログの読み込み） */
  listMessages: (roomId: number, beforeId?: number) => {
    const params = new URLSearchParams({ limit: String(MESSAGE_PAGE_SIZE) });
    if (beforeId !== undefined) params.set("before_id", String(beforeId));
    return request<MessageListResponse>(`/api/rooms/${roomId}/messages?${params}`);
  },
  postText: (roomId: number, content: string) =>
    request<Message>(`/api/rooms/${roomId}/messages`, { method: "POST", body: { content } }),
  postImage: (roomId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<Message>(`/api/rooms/${roomId}/messages/images`, { method: "POST", body: form });
  },
  deleteMessage: (roomId: number, messageId: number) =>
    request<Message>(`/api/rooms/${roomId}/messages/${messageId}`, { method: "DELETE" }),
};
