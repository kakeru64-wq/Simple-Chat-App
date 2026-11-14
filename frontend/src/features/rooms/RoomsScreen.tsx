"use client";

import { useRouter } from "next/navigation";
import { type ReactNode, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import { ErrorMessage } from "@/components/ErrorMessage";
import { useAuthedSession } from "@/features/auth/SessionGuard";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { api } from "@/lib/api";
import type { Room } from "@/lib/types";

import { AvailableRoomList } from "./AvailableRoomList";
import { CreateRoomForm } from "./CreateRoomForm";
import { JoinedRoomList } from "./JoinedRoomList";
import { RoomSearchBox } from "./RoomSearchBox";
import { useRooms } from "./useRooms";

/** 入力が止まってから検索するまでの待ち時間 */
const SEARCH_DEBOUNCE_MS = 300;

/** トーク一覧画面：ルーム作成・検索、参加中のトーク、参加できるルーム */
export function RoomsScreen() {
  const { user } = useAuthedSession();
  const router = useRouter();
  const [searchInput, setSearchInput] = useState("");
  const query = useDebouncedValue(searchInput.trim(), SEARCH_DEBOUNCE_MS);
  const { rooms, error: loadError } = useRooms(query);
  const [joiningId, setJoiningId] = useState<number | null>(null);
  const joinAction = useAsyncAction();

  const openRoom = (room: Room) => router.push(`/rooms/${room.id}`);

  const join = async (room: Room) => {
    setJoiningId(room.id);
    const ok = await joinAction.run(() => api.joinRoom(room.id), "参加に失敗しました");
    if (ok) openRoom(room);
    else setJoiningId(null);
  };

  const error = joinAction.error ?? loadError;
  const emptyMessage = query ? `「${query}」に一致するルームはありません` : undefined;

  return (
    <div className="flex min-h-dvh flex-col bg-gray-50">
      <AppHeader title="トーク" userName={user.name} />
      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-4 p-4">
        <section className="rounded-lg bg-white p-4 shadow-sm">
          <CreateRoomForm onCreated={openRoom} />
        </section>

        <RoomSearchBox value={searchInput} onChange={setSearchInput} />

        <ErrorMessage message={error} className="rounded-lg bg-red-50 p-3 text-sm" />

        {rooms === null ? (
          !error && <p className="py-8 text-center text-sm text-gray-500">読み込み中...</p>
        ) : (
          <>
            <Section title="参加中のトーク">
              <JoinedRoomList
                rooms={rooms.filter((r) => r.is_member)}
                myUserId={user.id}
                emptyMessage={emptyMessage}
              />
            </Section>
            <Section title="参加できるルーム">
              <AvailableRoomList
                rooms={rooms.filter((r) => !r.is_member)}
                joiningId={joiningId}
                onJoin={join}
                emptyMessage={emptyMessage}
              />
            </Section>
          </>
        )}
      </main>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="overflow-hidden rounded-lg bg-white shadow-sm">
      <h2 className="border-b border-gray-100 px-4 py-2 text-xs font-bold text-gray-500">
        {title}
      </h2>
      {children}
    </section>
  );
}
