"use client";

import { useConnectionStatus } from "@/features/realtime/RealtimeProvider";

/** WebSocket が繋がっていないときだけ、ヘッダーに状態を表示する */
export function ConnectionBadge() {
  const status = useConnectionStatus();
  if (status === "open") return null;
  return (
    <span className="shrink-0 rounded bg-yellow-400/90 px-1.5 py-0.5 text-[10px] font-normal text-black">
      {status === "connecting" ? "接続中..." : "再接続待ち"}
    </span>
  );
}
