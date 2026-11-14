import Link from "next/link";
import type { ReactNode } from "react";

import { formatListTime, formatUnread, previewText } from "@/lib/format";
import type { Room } from "@/lib/types";

function RoomIcon() {
  return (
    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#06C755]/15 font-bold text-[#06C755]">
      #
    </div>
  );
}

/** 参加中のトーク一覧（LINE のトーク一覧風：最新メッセージと未読数を表示） */
type JoinedProps = {
  rooms: Room[];
  myUserId: number;
  /** 0 件のときの表示（検索中など）。省略時は既定の案内 */
  emptyMessage?: ReactNode;
};

export function JoinedRoomList({ rooms, myUserId, emptyMessage }: JoinedProps) {
  if (rooms.length === 0) {
    return (
      <p className="px-4 py-8 text-center text-sm text-gray-500">
        {emptyMessage ?? (
          <>
            参加中のルームはありません。
            <br />
            上のフォームから作成するか、下の一覧から参加してください。
          </>
        )}
      </p>
    );
  }
  return (
    <ul className="divide-y divide-gray-100">
      {rooms.map((room) => (
        <li key={room.id}>
          <Link
            href={`/rooms/${room.id}`}
            className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50"
          >
            <RoomIcon />
            <div className="flex min-w-0 flex-1 flex-col gap-0.5">
              <div className="flex items-baseline gap-2">
                <span className="truncate font-bold">{room.name}</span>
                <span className="shrink-0 text-xs text-gray-400">({room.member_count})</span>
              </div>
              <p className="truncate text-sm text-gray-500">
                {room.last_message
                  ? previewText(room.last_message, myUserId)
                  : "まだメッセージはありません"}
              </p>
            </div>
            <div className="flex shrink-0 flex-col items-end gap-1">
              <span className="text-xs text-gray-400">
                {room.last_message ? formatListTime(room.last_message.created_at) : ""}
              </span>
              {room.unread_count > 0 && (
                <span
                  aria-label={`未読 ${room.unread_count} 件`}
                  className="min-w-5 rounded-full bg-[#06C755] px-1.5 text-center text-xs leading-5 font-bold text-white"
                >
                  {formatUnread(room.unread_count)}
                </span>
              )}
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}

type AvailableProps = {
  rooms: Room[];
  joiningId: number | null;
  onJoin: (room: Room) => void;
  emptyMessage?: ReactNode;
};

/** 未参加のルーム一覧（参加ボタン付き） */
export function AvailableRoomList({ rooms, joiningId, onJoin, emptyMessage }: AvailableProps) {
  if (rooms.length === 0) {
    return (
      <p className="px-4 py-6 text-center text-sm text-gray-500">
        {emptyMessage ?? "参加できるルームはありません"}
      </p>
    );
  }
  return (
    <ul className="divide-y divide-gray-100">
      {rooms.map((room) => (
        <li key={room.id} className="flex items-center gap-3 px-4 py-3">
          <RoomIcon />
          <div className="flex min-w-0 flex-1 items-baseline gap-2">
            <span className="truncate font-medium">{room.name}</span>
            <span className="shrink-0 text-xs text-gray-400">{room.member_count}人</span>
          </div>
          <button
            type="button"
            onClick={() => onJoin(room)}
            disabled={joiningId !== null}
            className="shrink-0 rounded-full border border-[#06C755] px-4 py-1 text-sm font-bold text-[#06C755] hover:bg-[#06C755]/10 disabled:opacity-50"
          >
            {joiningId === room.id ? "参加中..." : "参加"}
          </button>
        </li>
      ))}
    </ul>
  );
}
