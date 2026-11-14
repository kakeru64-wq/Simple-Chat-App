"use client";

import { useRouter } from "next/navigation";

import { AppHeader } from "@/components/AppHeader";
import { Button } from "@/components/Button";
import { ErrorMessage } from "@/components/ErrorMessage";
import { useAuthedSession } from "@/features/auth/SessionGuard";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import { api } from "@/lib/api";
import type { Message, Room } from "@/lib/types";

import { ConnectionBadge } from "./ConnectionBadge";
import { MessageInput } from "./MessageInput";
import { MessageList } from "./MessageList";
import { RoomNameEditor } from "./RoomNameEditor";
import { useRoomMessages } from "./useRoomMessages";

type Props = {
  room: Room;
  /** 名前変更などでルーム情報が変わったとき */
  onRoomChange: (room: Room) => void;
};

/** 参加中のルームのチャット画面：ヘッダー（名前変更・退会）、メッセージ一覧、送信フォーム */
export function ChatView({ room, onRoomChange }: Props) {
  const { user } = useAuthedSession();
  const router = useRouter();
  const chat = useRoomMessages(room.id);
  const action = useAsyncAction(); // 取り消し・退会

  const handleDelete = (message: Message) => {
    if (!window.confirm("このメッセージの送信を取り消しますか？\n相手の画面からも消えます。")) {
      return;
    }
    void action.run(() => chat.remove(message.id), "取り消しに失敗しました");
  };

  const handleLeave = async () => {
    const confirmText = `「${room.name}」から退会しますか？\n退会するとメッセージを見られなくなります。`;
    if (!window.confirm(confirmText)) return;
    const ok = await action.run(() => api.leaveRoom(room.id), "退会に失敗しました");
    if (ok) router.push("/rooms");
  };

  // 失敗時のエラー表示は RoomNameEditor が行う
  const handleRename = async (name: string) => onRoomChange(await api.renameRoom(room.id, name));

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
            <ConnectionBadge />
          </span>
        }
        actions={
          <Button variant="header" onClick={handleLeave} disabled={action.isPending}>
            退会
          </Button>
        }
      />

      <ErrorMessage
        message={action.error ?? chat.error}
        className="bg-red-50 px-4 py-1 text-center text-xs"
      />

      {chat.isLoading ? (
        <div className="flex flex-1 items-center justify-center bg-chat text-sm text-white">
          読み込み中...
        </div>
      ) : (
        <MessageList
          messages={chat.messages}
          myUserId={user.id}
          hasMore={chat.hasMore}
          isLoadingOlder={chat.isLoadingOlder}
          onLoadOlder={chat.loadOlder}
          onDelete={handleDelete}
        />
      )}

      <MessageInput
        onSendText={chat.sendText}
        onSendImage={chat.sendImage}
        disabled={chat.isLoading || action.isPending}
      />
    </div>
  );
}
