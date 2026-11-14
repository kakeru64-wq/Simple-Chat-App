"use client";

import { useEffect, useState } from "react";

import { useRealtimeEvent } from "@/features/realtime/RealtimeProvider";
import { ApiError, api, getErrorMessage } from "@/lib/api";
import type { Room } from "@/lib/types";

export type RoomState =
  | { kind: "loading" }
  | { kind: "not-found" }
  | { kind: "error"; message: string }
  | { kind: "ready"; room: Room };

/**
 * チャット画面のルーム情報を取得する。
 * 他の参加者による名前変更・参加・退会（room.updated）もリアルタイムに反映する。
 */
export function useRoom(roomId: number) {
  const [state, setState] = useState<RoomState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;
    api
      .getRoom(roomId)
      .then((room) => !cancelled && setState({ kind: "ready", room }))
      .catch((e) => {
        if (cancelled) return;
        setState(
          e instanceof ApiError && e.status === 404
            ? { kind: "not-found" }
            : { kind: "error", message: getErrorMessage(e, "読み込みに失敗しました") },
        );
      });
    return () => {
      cancelled = true;
    };
  }, [roomId]);

  useRealtimeEvent((event) => {
    if (event.type !== "room.updated" || event.room.id !== roomId) return;
    setState((prev) =>
      prev.kind === "ready" ? { kind: "ready", room: { ...prev.room, ...event.room } } : prev,
    );
  });

  /** 自分の操作（参加・名前変更）の結果で置き換える */
  const setRoom = (room: Room) => setState({ kind: "ready", room });

  return { state, setRoom };
}
