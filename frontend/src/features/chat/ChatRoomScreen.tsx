"use client";

import { useParams } from "next/navigation";

import { BackToRoomsLink, CenteredScreen } from "@/components/CenteredScreen";

import { ChatView } from "./ChatView";
import { JoinPrompt } from "./JoinPrompt";
import { useRoom } from "./useRoom";

/** チャット画面（/rooms/[roomId]）。URL のルーム ID を読み取る。 */
export function ChatRoomScreen() {
  const { roomId } = useParams<{ roomId: string }>();
  const id = Number(roomId);

  if (!Number.isInteger(id) || id <= 0) {
    return <p className="p-8 text-center text-gray-600">不正なルーム ID です</p>;
  }
  // key を変えることで、別のルームへ移動したときに state をすべて作り直す
  return <ChatRoom key={id} roomId={id} />;
}

/** ルームの状態に応じて、チャット・参加の案内・エラーを出し分ける */
function ChatRoom({ roomId }: { roomId: number }) {
  const { state, setRoom } = useRoom(roomId);

  switch (state.kind) {
    case "loading":
      return <CenteredScreen title="…">読み込み中...</CenteredScreen>;
    case "not-found":
      return (
        <CenteredScreen title="ルームが見つかりません">
          <p>このルームは存在しません。</p>
          <BackToRoomsLink />
        </CenteredScreen>
      );
    case "error":
      return (
        <CenteredScreen title="エラー">
          <p>{state.message}</p>
          <BackToRoomsLink />
        </CenteredScreen>
      );
    case "ready":
      return state.room.is_member ? (
        <ChatView room={state.room} onRoomChange={setRoom} />
      ) : (
        <JoinPrompt room={state.room} onJoined={setRoom} />
      );
  }
}
