import { Suspense } from "react";

import { ChatRoomScreen } from "@/components/ChatRoomScreen";

// ルーム ID はリクエスト時まで確定しないため、useParams を使う部分を Suspense で囲む
// (cacheComponents 有効時の要件)
export default function ChatRoomPage() {
  return (
    <Suspense>
      <ChatRoomScreen />
    </Suspense>
  );
}
