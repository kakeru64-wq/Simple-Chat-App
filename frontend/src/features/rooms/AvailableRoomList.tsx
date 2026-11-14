import type { ReactNode } from "react";

import { Button } from "@/components/Button";
import type { Room } from "@/lib/types";

import { RoomIcon } from "./RoomIcon";

type Props = {
  rooms: Room[];
  /** 参加処理中のルーム ID（処理中はすべてのボタンを無効にする） */
  joiningId: number | null;
  onJoin: (room: Room) => void;
  /** 0 件のときの表示（検索中など） */
  emptyMessage?: ReactNode;
};

/** 未参加のルーム一覧（参加ボタン付き） */
export function AvailableRoomList({ rooms, joiningId, onJoin, emptyMessage }: Props) {
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
          <Button
            variant="outline"
            onClick={() => onJoin(room)}
            disabled={joiningId !== null}
            className="rounded-full px-4 py-1 text-sm"
          >
            {joiningId === room.id ? "参加中..." : "参加"}
          </Button>
        </li>
      ))}
    </ul>
  );
}
