"use client";

import { type FormEvent, useState } from "react";

import { ApiError, api } from "@/lib/api";
import { LIMITS } from "@/lib/config";
import type { Room } from "@/lib/types";

export function CreateRoomForm({ onCreated }: { onCreated: (room: Room) => void }) {
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const trimmed = name.trim();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!trimmed || isSubmitting) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const room = await api.createRoom(trimmed);
      setName("");
      onCreated(room);
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 409
          ? "同じ名前のルームが既にあります"
          : err instanceof ApiError
            ? err.message
            : "ルームの作成に失敗しました",
      );
    } finally {
      setIsSubmitting(false);
    }
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
          className="min-w-0 flex-1 rounded-md border border-gray-300 px-3 py-2 outline-none focus:border-[#06C755] focus:ring-2 focus:ring-[#06C755]/30"
        />
        <button
          type="submit"
          disabled={!trimmed || isSubmitting}
          className="rounded-md bg-[#06C755] px-4 text-sm font-bold text-white hover:bg-[#05b14c] disabled:cursor-not-allowed disabled:opacity-50"
        >
          作成
        </button>
      </div>
      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}
    </form>
  );
}
