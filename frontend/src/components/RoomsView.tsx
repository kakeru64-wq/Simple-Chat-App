"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import { useAuthedSession } from "@/components/AuthenticatedShell";
import { CreateRoomForm } from "@/components/CreateRoomForm";
import { useRealtimeEvent } from "@/components/RealtimeProvider";
import { AvailableRoomList, JoinedRoomList } from "@/components/RoomList";
import { ApiError, api } from "@/lib/api";
import type { Room } from "@/lib/types";

/** ルーム一覧画面：参加中のトーク（最新メッセージ・未読数）と、参加できるルーム。 */
export function RoomsView() {
  const session = useAuthedSession();
  const router = useRouter();
  const [rooms, setRooms] = useState<Room[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [joiningId, setJoiningId] = useState<number | null>(null);

  const reload = useCallback(() => {
    api
      .listRooms()
      .then((data) => {
        setRooms(data);
        setError(null);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "ルーム一覧の取得に失敗しました"));
  }, []);

  useEffect(reload, [reload]);

  // 新着・削除・再接続のたびに取り直し、未読数と最新メッセージを最新にする
  useRealtimeEvent(reload);

  const join = async (room: Room) => {
    setJoiningId(room.id);
    try {
      await api.joinRoom(room.id);
      router.push(`/rooms/${room.id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "参加に失敗しました");
      setJoiningId(null);
    }
  };

  const joined = rooms?.filter((r) => r.is_member) ?? [];
  const available = rooms?.filter((r) => !r.is_member) ?? [];

  return (
    <div className="flex min-h-dvh flex-col bg-gray-50">
      <AppHeader title="トーク" userName={session.user.name} />
      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-4 p-4">
        <section className="rounded-lg bg-white p-4 shadow-sm">
          <CreateRoomForm onCreated={(room) => router.push(`/rooms/${room.id}`)} />
        </section>

        {error && (
          <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
            {error}
          </p>
        )}

        {rooms === null ? (
          !error && <p className="py-8 text-center text-sm text-gray-500">読み込み中...</p>
        ) : (
          <>
            <RoomSection title="参加中のトーク">
              <JoinedRoomList rooms={joined} myUserId={session.user.id} />
            </RoomSection>
            <RoomSection title="参加できるルーム">
              <AvailableRoomList rooms={available} joiningId={joiningId} onJoin={join} />
            </RoomSection>
          </>
        )}
      </main>
    </div>
  );
}

function RoomSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="overflow-hidden rounded-lg bg-white shadow-sm">
      <h2 className="border-b border-gray-100 px-4 py-2 text-xs font-bold text-gray-500">
        {title}
      </h2>
      {children}
    </section>
  );
}
