import Link from "next/link";

import type { Room } from "@/lib/types";

export function RoomList({ rooms }: { rooms: Room[] }) {
  if (rooms.length === 0) {
    return <p className="py-8 text-center text-sm text-gray-500">ルームがありません</p>;
  }
  return (
    <ul className="divide-y divide-gray-100">
      {rooms.map((room) => (
        <li key={room.id}>
          <Link
            href={`/rooms/${room.id}`}
            className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50"
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#06C755]/15 font-bold text-[#06C755]">
              #
            </div>
            <span className="min-w-0 flex-1 truncate font-medium">{room.name}</span>
            <span aria-hidden className="text-gray-400">
              ›
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
