"use client";

import { useParams } from "next/navigation";

import { ChatRoom } from "@/components/ChatRoom";
import { useRequireSession } from "@/hooks/useSession";

/** URL からルーム ID を読み取り、ログイン確認後にチャット画面を表示する。 */
export function ChatRoomScreen() {
  const { roomId } = useParams<{ roomId: string }>();
  const session = useRequireSession();
  const id = Number(roomId);

  if (!session) return null; // 判定中 or リダイレクト中
  if (!Number.isInteger(id) || id <= 0) {
    return <p className="p-8 text-center text-gray-600">不正なルーム ID です</p>;
  }
  // key を変えることで、ルーム移動時にメッセージ等の state をリセットする
  return <ChatRoom key={id} roomId={id} session={session} />;
}
