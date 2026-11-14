"use client";

import { useCallback, useEffect, useState } from "react";

import { useRealtimeEvent } from "@/components/RealtimeProvider";
import { ApiError, api } from "@/lib/api";
import { mergeMessages } from "@/lib/format";
import type { Message } from "@/lib/types";

function toErrorMessage(e: unknown, fallback: string): string {
  return e instanceof ApiError ? e.message : fallback;
}

/**
 * ルームのメッセージを管理するフック（参加中のルームでのみ使う）。
 * - 初回は REST で最新ページを取得し、新着・削除は WebSocket イベントで反映
 * - 再接続時は REST で最新ページを取り直して取りこぼしを補完
 * - REST と WebSocket の両方から同じメッセージが届くため id で重複排除する
 * - 表示中の最新メッセージまでを既読にする（タブが表示されているときのみ）
 *
 * ルームが変わったときは呼び出し側で key を変えて state ごと作り直す想定。
 */
export function useRoomMessages(roomId: number) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingOlder, setIsLoadingOlder] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const applyIncoming = useCallback((incoming: Message[]) => {
    setMessages((prev) => mergeMessages(prev, incoming));
  }, []);

  // 初回取得
  useEffect(() => {
    let cancelled = false;
    api
      .listMessages(roomId)
      .then((res) => {
        if (cancelled) return;
        applyIncoming(res.messages);
        setHasMore(res.has_more);
      })
      .catch((e) => !cancelled && setError(toErrorMessage(e, "メッセージの取得に失敗しました")))
      .finally(() => !cancelled && setIsLoading(false));
    return () => {
      cancelled = true;
    };
  }, [roomId, applyIncoming]);

  useRealtimeEvent((event) => {
    if (event.type === "connection.opened") {
      // 再接続：切断中のメッセージを補完（has_more は既に読んだ過去ページを考慮して維持）
      api
        .listMessages(roomId)
        .then((res) => applyIncoming(res.messages))
        .catch(() => {});
      return;
    }
    if (event.message.room_id === roomId) applyIncoming([event.message]);
  });

  // 既読位置の更新
  const latestId = messages.at(-1)?.id;
  useEffect(() => {
    if (latestId === undefined) return;
    const markRead = () => {
      if (document.visibilityState === "visible") {
        api.markRead(roomId, latestId).catch(() => {});
      }
    };
    markRead();
    document.addEventListener("visibilitychange", markRead);
    return () => document.removeEventListener("visibilitychange", markRead);
  }, [roomId, latestId]);

  const loadOlder = useCallback(async () => {
    const oldest = messages[0];
    if (!oldest || isLoadingOlder) return;
    setIsLoadingOlder(true);
    try {
      const res = await api.listMessages(roomId, oldest.id);
      applyIncoming(res.messages);
      setHasMore(res.has_more);
    } catch (e) {
      setError(toErrorMessage(e, "メッセージの取得に失敗しました"));
    } finally {
      setIsLoadingOlder(false);
    }
  }, [roomId, messages, isLoadingOlder, applyIncoming]);

  // 送信・削除は WebSocket の到着を待たず、レスポンスで即座に反映する（失敗時は例外を呼び出し側へ）
  const send = useCallback(
    async (content: string) => applyIncoming([await api.postMessage(roomId, content)]),
    [roomId, applyIncoming],
  );
  const sendImage = useCallback(
    async (file: File) => applyIncoming([await api.postImage(roomId, file)]),
    [roomId, applyIncoming],
  );
  const remove = useCallback(
    async (messageId: number) => applyIncoming([await api.deleteMessage(roomId, messageId)]),
    [roomId, applyIncoming],
  );

  return {
    messages,
    hasMore,
    isLoading,
    isLoadingOlder,
    error,
    loadOlder,
    send,
    sendImage,
    remove,
  };
}
