"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppHeader, headerButtonClass } from "@/components/AppHeader";
import { useAuthedSession } from "@/components/AuthenticatedShell";
import { MessageInput } from "@/components/MessageInput";
import { MessageList } from "@/components/MessageList";
import {
  type ConnectionStatus,
  useConnectionStatus,
  useRealtimeEvent,
} from "@/components/RealtimeProvider";
import { RoomNameEditor } from "@/components/RoomNameEditor";
import { useRoomMessages } from "@/hooks/useRoomMessages";
import { ApiError, api } from "@/lib/api";
import type { Message, Room } from "@/lib/types";

type LoadState =
  | { kind: "loading" }
  | { kind: "not-found" }
  | { kind: "error"; message: string }
  | { kind: "ready"; room: Room };

/** チャットルーム画面。ルーム情報を取得し、参加状態に応じて表示を切り替える。 */
export function ChatRoom({ roomId }: { roomId: number }) {
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;
    api
      .getRoom(roomId)
      .then((room) => !cancelled && setState({ kind: "ready", room }))
      .catch((e) => {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 404) setState({ kind: "not-found" });
        else
          setState({
            kind: "error",
            message: e instanceof ApiError ? e.message : "読み込みに失敗しました",
          });
      });
    return () => {
      cancelled = true;
    };
  }, [roomId]);

  // 他の参加者による名前変更・参加・退会（人数）を反映する
  useRealtimeEvent((event) => {
    if (event.type !== "room.updated" || event.room.id !== roomId) return;
    setState((prev) =>
      prev.kind === "ready" ? { kind: "ready", room: { ...prev.room, ...event.room } } : prev,
    );
  });

  const updateRoom = (room: Room) => setState({ kind: "ready", room });

  switch (state.kind) {
    case "loading":
      return <CenteredScreen title="…">読み込み中...</CenteredScreen>;
    case "not-found":
      return (
        <CenteredScreen title="ルームが見つかりません">
          <p>このルームは存在しません。</p>
          <BackToRooms />
        </CenteredScreen>
      );
    case "error":
      return (
        <CenteredScreen title="エラー">
          <p>{state.message}</p>
          <BackToRooms />
        </CenteredScreen>
      );
    case "ready":
      return state.room.is_member ? (
        <ChatRoomBody room={state.room} onRoomChange={updateRoom} />
      ) : (
        <JoinPrompt room={state.room} onJoined={updateRoom} />
      );
  }
}

/** 参加中のルーム：メッセージ一覧と送信フォーム */
function ChatRoomBody({ room, onRoomChange }: { room: Room; onRoomChange: (room: Room) => void }) {
  const session = useAuthedSession();
  const router = useRouter();
  const connection = useConnectionStatus();
  const [actionError, setActionError] = useState<string | null>(null);
  const [isLeaving, setIsLeaving] = useState(false);
  const {
    messages,
    hasMore,
    isLoading,
    isLoadingOlder,
    error,
    loadOlder,
    send,
    sendImage,
    remove,
  } = useRoomMessages(room.id);

  const handleDelete = async (message: Message) => {
    if (!window.confirm("このメッセージの送信を取り消しますか？\n相手の画面からも消えます。"))
      return;
    setActionError(null);
    try {
      await remove(message.id);
    } catch (e) {
      setActionError(e instanceof ApiError ? e.message : "取り消しに失敗しました");
    }
  };

  const handleLeave = async () => {
    if (
      !window.confirm(
        `「${room.name}」から退会しますか？\n退会するとメッセージを見られなくなります。`,
      )
    )
      return;
    setIsLeaving(true);
    try {
      await api.leaveRoom(room.id);
      router.push("/rooms");
    } catch (e) {
      setActionError(e instanceof ApiError ? e.message : "退会に失敗しました");
      setIsLeaving(false);
    }
  };

  const handleRename = async (name: string) => {
    onRoomChange(await api.renameRoom(room.id, name)); // 失敗時の表示は RoomNameEditor が行う
  };

  const displayError = actionError ?? error;

  return (
    <div className="flex h-dvh flex-col">
      <AppHeader
        backHref="/rooms"
        title={
          <span className="flex items-center gap-2">
            <RoomNameEditor name={room.name} onRename={handleRename} />
            <span className="shrink-0 text-xs font-normal text-white/70">
              ({room.member_count})
            </span>
            <ConnectionBadge status={connection} />
          </span>
        }
        actions={
          <button
            type="button"
            onClick={handleLeave}
            disabled={isLeaving}
            className={headerButtonClass}
          >
            退会
          </button>
        }
      />

      {displayError && (
        <p role="alert" className="bg-red-50 px-4 py-1 text-center text-xs text-red-600">
          {displayError}
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
          onDelete={handleDelete}
        />
      )}

      <MessageInput onSend={send} onSendImage={sendImage} disabled={isLoading || isLeaving} />
    </div>
  );
}

/** 未参加のルームを開いたとき：参加を促す */
function JoinPrompt({ room, onJoined }: { room: Room; onJoined: (room: Room) => void }) {
  const [isJoining, setIsJoining] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const join = async () => {
    setIsJoining(true);
    setError(null);
    try {
      onJoined(await api.joinRoom(room.id));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "参加に失敗しました");
      setIsJoining(false);
    }
  };

  return (
    <CenteredScreen title={room.name}>
      <p className="text-lg font-bold text-gray-800">{room.name}</p>
      <p className="text-sm">{room.member_count}人が参加中</p>
      <button
        type="button"
        onClick={join}
        disabled={isJoining}
        className="rounded-md bg-[#06C755] px-8 py-2.5 font-bold text-white hover:bg-[#05b14c] disabled:opacity-50"
      >
        {isJoining ? "参加中..." : "参加する"}
      </button>
      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}
      <BackToRooms />
    </CenteredScreen>
  );
}

function CenteredScreen({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex h-dvh flex-col">
      <AppHeader title={title} backHref="/rooms" />
      <div className="flex flex-1 flex-col items-center justify-center gap-4 bg-gray-50 p-4 text-center text-gray-600">
        {children}
      </div>
    </div>
  );
}

function BackToRooms() {
  return (
    <Link href="/rooms" className="text-sm text-[#06C755] underline">
      トーク一覧へ戻る
    </Link>
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
