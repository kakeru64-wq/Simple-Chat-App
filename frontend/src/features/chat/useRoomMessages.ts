"use client";

import { useCallback, useEffect, useState } from "react";

import { useRealtimeEvent } from "@/features/realtime/RealtimeProvider";
import { api, getErrorMessage } from "@/lib/api";
import { mergeMessages } from "@/lib/messages";
import type { Message } from "@/lib/types";

const LOAD_ERROR = "メッセージの取得に失敗しました";

/**
 * 参加中のルームのメッセージを管理する。
 *
 * - 最初に REST で最新ページを取得し、新着・取り消しは WebSocket のイベントで反映する
 * - WebSocket の再接続時は最新ページを取り直し、切断中のメッセージを補完する
 * - REST と WebSocket の両方から同じメッセージが届くので、id で重複を除く（mergeMessages）
 * - 表示している最新メッセージまでを既読にする（タブが表示されているときだけ）
 * - 送信・取り消しは WebSocket を待たず、API のレスポンスですぐ画面に反映する
 */
export function useRoomMessages(roomId: number) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingOlder, setIsLoadingOlder] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apply = useCallback((incoming: Message[]) => {
    setMessages((prev) => mergeMessages(prev, incoming));
  }, []);

  // ---- 最初の読み込み ----
  useEffect(() => {
    let cancelled = false;
    api
      .listMessages(roomId)
      .then((res) => {
        if (cancelled) return;
        apply(res.messages);
        setHasMore(res.has_more);
      })
      .catch((e) => !cancelled && setError(getErrorMessage(e, LOAD_ERROR)))
      .finally(() => !cancelled && setIsLoading(false));
    return () => {
      cancelled = true;
    };
  }, [roomId, apply]);

  // ---- リアルタイム反映 ----
  useRealtimeEvent((event) => {
    if (event.type === "connection.opened") {
      // 再接続：切断中のメッセージを補完する（読み込み済みの過去ページは残す）
      api
        .listMessages(roomId)
        .then((res) => apply(res.messages))
        .catch(() => {});
    } else if (event.type !== "room.updated" && event.message.room_id === roomId) {
      apply([event.message]);
    }
  });

  // ---- 既読 ----
  const latestId = messages.at(-1)?.id;
  useEffect(() => {
    if (latestId === undefined) return;
    const markRead = () => {
      if (document.visibilityState === "visible") {
        api.markRead(roomId, latestId).catch(() => {});
      }
    };
    markRead();
    document.addEventListener("visibilitychange", markRead); // 別タブから戻ったとき
    return () => document.removeEventListener("visibilitychange", markRead);
  }, [roomId, latestId]);

  // ---- 操作 ----
  const loadOlder = useCallback(async () => {
    const oldest = messages[0];
    if (!oldest || isLoadingOlder) return;
    setIsLoadingOlder(true);
    try {
      const res = await api.listMessages(roomId, oldest.id);
      apply(res.messages);
      setHasMore(res.has_more);
    } catch (e) {
      setError(getErrorMessage(e, LOAD_ERROR));
    } finally {
      setIsLoadingOlder(false);
    }
  }, [roomId, messages, isLoadingOlder, apply]);

  // 以下は失敗時に例外をそのまま投げる（エラー表示は呼び出し側）
  const sendText = useCallback(
    async (content: string) => apply([await api.postText(roomId, content)]),
    [roomId, apply],
  );
  const sendImage = useCallback(
    async (file: File) => apply([await api.postImage(roomId, file)]),
    [roomId, apply],
  );
  const remove = useCallback(
    async (messageId: number) => apply([await api.deleteMessage(roomId, messageId)]),
    [roomId, apply],
  );

  return {
    messages,
    hasMore,
    isLoading,
    isLoadingOlder,
    error,
    loadOlder,
    sendText,
    sendImage,
    remove,
  };
}
