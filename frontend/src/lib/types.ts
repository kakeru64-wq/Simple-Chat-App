/** バックエンド API のレスポンス型（backend/app/schemas.py と対応） */

export type User = {
  id: number;
  name: string;
  created_at: string;
};

export type Message = {
  id: number;
  room_id: number;
  user: User;
  /** テキスト本文。画像メッセージ・削除済みは null */
  content: string | null;
  /** API サーバーからの相対パス。画像でなければ null */
  image_url: string | null;
  is_deleted: boolean;
  created_at: string;
};

/** ルーム情報 + 閲覧ユーザーから見た状態 */
export type Room = {
  id: number;
  name: string;
  created_at: string;
  member_count: number;
  is_member: boolean;
  unread_count: number;
  last_message: Message | null;
};

export type LoginResponse = {
  token: string;
  user: User;
};

export type MessageListResponse = {
  messages: Message[];
  has_more: boolean;
};

/** WebSocket で受信するイベント */
export type ChatMessageEvent = {
  type: "message.created" | "message.deleted";
  message: Message;
};

/** ルーム情報の変更（名前変更など）。全参加者に共通の情報のみ含む */
export type RoomUpdatedEvent = {
  type: "room.updated";
  room: Pick<Room, "id" | "name">;
};

export type ServerEvent = ChatMessageEvent | RoomUpdatedEvent;

/** クライアント側で発行するイベント（接続・再接続時。取りこぼしの補完に使う） */
export type ConnectionOpenedEvent = { type: "connection.opened" };

export type RealtimeEvent = ServerEvent | ConnectionOpenedEvent;

/** ブラウザに保存するログイン情報 */
export type Session = {
  token: string;
  user: User;
};
