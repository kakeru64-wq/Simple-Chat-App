"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { useRealtimeEvent } from "@/features/realtime/RealtimeProvider";
import { api, getErrorMessage } from "@/lib/api";
import type { Room } from "@/lib/types";

/**
 * トーク一覧に表示するルームを取得する。query を渡すとルーム名で検索する。
 * 新着・取り消し・名前変更・再接続などのイベントが届くたびに取り直し、未読数や最新メッセージを最新に保つ。
 */
export function useRooms(query: string) {
  const [rooms, setRooms] = useState<Room[] | null>(null); // null = 読み込み中
  const [error, setError] = useState<string | null>(null);
  // 連続して検索したとき、古いレスポンスで新しい結果を上書きしないための連番
  const latestRequestRef = useRef(0);

  const reload = useCallback(() => {
    const requestId = ++latestRequestRef.current;
    api
      .listRooms(query)
      .then((data) => {
        if (requestId !== latestRequestRef.current) return;
        setRooms(data);
        setError(null);
      })
      .catch((e) => setError(getErrorMessage(e, "ルーム一覧の取得に失敗しました")));
  }, [query]);

  useEffect(reload, [reload]);
  useRealtimeEvent(reload);

  return { rooms, error };
}
