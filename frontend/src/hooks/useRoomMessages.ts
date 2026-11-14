"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";
import { WS_BASE_URL } from "@/lib/config";
import { mergeMessages } from "@/lib/format";
import { clearSession } from "@/lib/session";
import type { Message, RoomEvent } from "@/lib/types";

export type ConnectionStatus = "connecting" | "open" | "closed";

// バックエンド (app/routers/ws.py) と対応するクローズコード
const WS_CLOSE_UNAUTHORIZED = 4401;
const WS_CLOSE_NOT_FOUND = 4404;
const MAX_RECONNECT_DELAY_MS = 10_000;

/**
 * ルームのメッセージを管理するフック。
 * - WebSocket 接続のたびに REST で最新ページを取得（購読開始前・切断中の取りこぼしを補完）
 * - 新着は WebSocket で受信（切断時は指数バックオフで再接続）
 * - REST と WebSocket の両方から同じメッセージが届くため id で重複排除する
 *
 * ルームが変わったときは呼び出し側で key を変えて state ごと作り直す想定。
 */
export function useRoomMessages(roomId: number, token: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingOlder, setIsLoadingOlder] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connection, setConnection] = useState<ConnectionStatus>("connecting");

  const fetchLatest = useCallback(async () => {
    try {
      const res = await api.listMessages(roomId);
      setMessages((prev) => mergeMessages(prev, res.messages));
      // 再接続時の補完では has_more を上書きしない（既に古いページを読んでいる可能性がある）
      setHasMore((prev) => prev || res.has_more);
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "メッセージの取得に失敗しました");
    } finally {
      setIsLoading(false);
    }
  }, [roomId]);

  // WebSocket 購読
  useEffect(() => {
    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let attempt = 0;
    let disposed = false;
    let hasFetched = false;

    const connect = () => {
      ws = new WebSocket(`${WS_BASE_URL}/ws/rooms/${roomId}?token=${encodeURIComponent(token)}`);

      ws.onopen = () => {
        setConnection("open");
        // 購読開始前・切断中に投稿されたメッセージを補完する
        hasFetched = true;
        void fetchLatest();
        attempt = 0;
      };

      ws.onmessage = (e: MessageEvent<string>) => {
        const event = JSON.parse(e.data) as RoomEvent;
        if (event.type === "message.created") {
          setMessages((prev) => mergeMessages(prev, [event.message]));
        }
      };

      ws.onclose = (e) => {
        if (disposed) return;
        setConnection("closed");
        // WebSocket が一度も繋がらない場合でも、履歴だけは REST で表示する
        if (!hasFetched) {
          hasFetched = true;
          void fetchLatest();
        }
        if (e.code === WS_CLOSE_UNAUTHORIZED) {
          clearSession(); // ガードによりログイン画面へ戻る
          return;
        }
        if (e.code === WS_CLOSE_NOT_FOUND) return;

        const delay = Math.min(1000 * 2 ** attempt, MAX_RECONNECT_DELAY_MS);
        attempt += 1;
        retryTimer = setTimeout(() => {
          setConnection("connecting");
          connect();
        }, delay);
      };
    };

    connect();
    return () => {
      disposed = true;
      clearTimeout(retryTimer);
      ws?.close();
    };
  }, [roomId, token, fetchLatest]);

  const loadOlder = useCallback(async () => {
    const oldest = messages[0];
    if (!oldest || isLoadingOlder) return;
    setIsLoadingOlder(true);
    try {
      const res = await api.listMessages(roomId, oldest.id);
      setMessages((prev) => mergeMessages(prev, res.messages));
      setHasMore(res.has_more);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "メッセージの取得に失敗しました");
    } finally {
      setIsLoadingOlder(false);
    }
  }, [roomId, messages, isLoadingOlder]);

  /** 送信。WebSocket の到着を待たず、レスポンスで即座に一覧へ反映する。 */
  const send = useCallback(
    async (content: string) => {
      const message = await api.postMessage(roomId, content);
      setMessages((prev) => mergeMessages(prev, [message]));
    },
    [roomId],
  );

  return { messages, hasMore, isLoading, isLoadingOlder, error, connection, loadOlder, send };
}
