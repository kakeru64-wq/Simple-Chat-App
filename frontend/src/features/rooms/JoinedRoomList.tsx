import Link from "next/link";
import type { ReactNode } from "react";

import { formatListTime } from "@/lib/datetime";
import { previewText } from "@/lib/messages";
import type { Room } from "@/lib/types";

import { RoomIcon } from "./RoomIcon";

type Props = {
  rooms: Room[];
  myUserId: number;
  /** 0 件のときの表示（検索中など）。省略時は既定の案内 */
  emptyMessage?: ReactNode;
};

/** 参加中のトーク一覧（LINE のトーク一覧風：最新メッセージ・時刻・未読数） */
export function JoinedRoomList({ rooms, myUserId, emptyMessage }: Props) {
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
                {room.last_message && formatListTime(room.last_message.created_at)}
              </span>
              <UnreadBadge count={room.unread_count} />
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}

function UnreadBadge({ count }: { count: number }) {
  if (count <= 0) return null;
  return (
    <span
      aria-label={`未読 ${count} 件`}
      className="min-w-5 rounded-full bg-[#06C755] px-1.5 text-center text-xs leading-5 font-bold text-white"
    >
      {count > 99 ? "99+" : count}
    </span>
  );
}
