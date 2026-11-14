"use client";

import { type FormEvent, useState } from "react";

import { Button } from "@/components/Button";
import { ErrorMessage } from "@/components/ErrorMessage";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import { api } from "@/lib/api";
import { LIMITS } from "@/lib/config";
import type { Room } from "@/lib/types";

/** 新しいルームを作るフォーム */
export function CreateRoomForm({ onCreated }: { onCreated: (room: Room) => void }) {
  const [name, setName] = useState("");
  const { run, isPending, error } = useAsyncAction();
  const trimmed = name.trim();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!trimmed || isPending) return;
    await run(async () => {
      const room = await api.createRoom(trimmed);
      setName("");
      onCreated(room);
    }, "ルームの作成に失敗しました");
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-1">
      <div className="flex gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={LIMITS.roomName}
          placeholder="新しいルーム名"
          aria-label="新しいルーム名"
          className="min-w-0 flex-1 rounded-md border border-gray-300 px-3 py-2 outline-none focus:border-brand focus:ring-2 focus:ring-brand/30"
        />
        <Button
          type="submit"
          variant="primary"
          disabled={!trimmed || isPending}
          className="rounded-md px-4 text-sm"
        >
          作成
        </Button>
      </div>
      <ErrorMessage message={error} />
    </form>
  );
}
