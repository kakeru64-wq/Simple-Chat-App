"use client";

import { useParams } from "next/navigation";

import { ChatRoom } from "@/components/ChatRoom";

/** URL からルーム ID を読み取り、チャット画面を表示する（ログイン確認はレイアウトで実施）。 */
export function ChatRoomScreen() {
  const { roomId } = useParams<{ roomId: string }>();
  const id = Number(roomId);

  if (!Number.isInteger(id) || id <= 0) {
    return <p className="p-8 text-center text-gray-600">不正なルーム ID です</p>;
  }
  // key を変えることで、ルーム移動時にメッセージ等の state をリセットする
  return <ChatRoom key={id} roomId={id} />;
}
