import { Suspense } from "react";

import { ChatRoomScreen } from "@/components/ChatRoomScreen";

// ルーム ID はリクエスト時まで確定しないため、useParams を使う部分を Suspense で囲んでおく
export default function ChatRoomPage() {
  return (
    <Suspense>
      <ChatRoomScreen />
    </Suspense>
  );
}
