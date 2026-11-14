import { Suspense } from "react";

import { ChatRoomScreen } from "@/features/chat/ChatRoomScreen";

// ルーム ID はリクエスト時まで決まらないため、useParams を使う部分を Suspense で囲む
export default function ChatRoomPage() {
  return (
    <Suspense>
      <ChatRoomScreen />
    </Suspense>
  );
}
