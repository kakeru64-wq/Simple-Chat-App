"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import { CreateRoomForm } from "@/components/CreateRoomForm";
import { RoomList } from "@/components/RoomList";
import { useRequireSession } from "@/hooks/useSession";
import { ApiError, api } from "@/lib/api";
import type { Room } from "@/lib/types";

/** ルーム一覧画面：既存ルームへの入室と新規作成。 */
export function RoomsView() {
  const session = useRequireSession();
  const router = useRouter();
  const [rooms, setRooms] = useState<Room[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!session) return;
    api
      .listRooms()
      .then(setRooms)
      .catch((e) =>
        setError(e instanceof ApiError ? e.message : "ルーム一覧の取得に失敗しました"),
      );
  }, [session]);

  if (!session) return null; // 判定中 or リダイレクト中

  return (
    <div className="flex min-h-dvh flex-col bg-gray-50">
      <AppHeader title="ルーム一覧" userName={session.user.name} />
      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-4 p-4">
        <section className="rounded-lg bg-white p-4 shadow-sm">
          <CreateRoomForm onCreated={(room) => router.push(`/rooms/${room.id}`)} />
        </section>
        <section className="overflow-hidden rounded-lg bg-white shadow-sm">
          {error ? (
            <p role="alert" className="p-4 text-sm text-red-600">
              {error}
            </p>
          ) : rooms === null ? (
            <p className="py-8 text-center text-sm text-gray-500">読み込み中...</p>
          ) : (
            <RoomList rooms={rooms} />
          )}
        </section>
      </main>
    </div>
  );
}
