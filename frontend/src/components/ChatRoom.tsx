"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import { MessageInput } from "@/components/MessageInput";
import { MessageList } from "@/components/MessageList";
import { type ConnectionStatus, useRoomMessages } from "@/hooks/useRoomMessages";
import { ApiError, api } from "@/lib/api";
import type { Room, Session } from "@/lib/types";

type Props = {
  roomId: number;
  session: Session;
};

/** チャットルーム画面の本体（メッセージ一覧＋送信フォーム）。 */
export function ChatRoom({ roomId, session }: Props) {
  const [room, setRoom] = useState<Room | null>(null);
  const [notFound, setNotFound] = useState(false);
  const { messages, hasMore, isLoading, isLoadingOlder, error, connection, loadOlder, send } =
    useRoomMessages(roomId, session.token);

  useEffect(() => {
    api
      .getRoom(roomId)
      .then(setRoom)
      .catch((e) => {
        if (e instanceof ApiError && e.status === 404) setNotFound(true);
      });
  }, [roomId]);

  if (notFound) {
    return (
      <div className="flex h-dvh flex-col">
        <AppHeader title="ルームが見つかりません" backHref="/rooms" userName={session.user.name} />
        <div className="flex flex-1 flex-col items-center justify-center gap-4 text-gray-600">
          <p>このルームは存在しません。</p>
          <Link href="/rooms" className="text-[#06C755] underline">
            ルーム一覧へ戻る
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-dvh flex-col">
      <AppHeader
        title={
          <span className="flex items-center gap-2">
            <span className="truncate">{room?.name ?? "…"}</span>
            <ConnectionBadge status={connection} />
          </span>
        }
        backHref="/rooms"
        userName={session.user.name}
      />

      {error && (
        <p role="alert" className="bg-red-50 px-4 py-1 text-center text-xs text-red-600">
          {error}
        </p>
      )}

      {isLoading ? (
        <div className="flex flex-1 items-center justify-center bg-[#8CABD9] text-sm text-white">
          読み込み中...
        </div>
      ) : (
        <MessageList
          messages={messages}
          myUserId={session.user.id}
          hasMore={hasMore}
          isLoadingOlder={isLoadingOlder}
          onLoadOlder={loadOlder}
        />
      )}

      <MessageInput onSend={send} disabled={isLoading} />
    </div>
  );
}

function ConnectionBadge({ status }: { status: ConnectionStatus }) {
  if (status === "open") return null;
  const label = status === "connecting" ? "接続中..." : "再接続待ち";
  return (
    <span className="shrink-0 rounded bg-yellow-400/90 px-1.5 py-0.5 text-[10px] font-normal text-black">
      {label}
    </span>
  );
}
