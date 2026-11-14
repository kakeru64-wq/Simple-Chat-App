/** バックエンド API のレスポンス型（backend/app/schemas.py と対応） */

export type User = {
  id: number;
  name: string;
  created_at: string;
};

export type Room = {
  id: number;
  name: string;
  created_at: string;
};

export type Message = {
  id: number;
  room_id: number;
  user: User;
  content: string;
  created_at: string;
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
export type RoomEvent = {
  type: "message.created";
  message: Message;
};

/** ブラウザに保存するログイン情報 */
export type Session = {
  token: string;
  user: User;
};
