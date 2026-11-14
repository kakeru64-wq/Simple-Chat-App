"use client";

import { Fragment, useLayoutEffect, useRef } from "react";

import { formatDate, isSameDay } from "@/lib/datetime";
import { noticeText } from "@/lib/messages";
import type { Message } from "@/lib/types";

import { MessageBubble } from "./MessageBubble";
import { SystemNotice } from "./SystemNotice";

type Props = {
  messages: Message[];
  myUserId: number;
  hasMore: boolean;
  isLoadingOlder: boolean;
  onLoadOlder: () => Promise<void>;
  onDelete: (message: Message) => void;
};

/** 下端から何 px 以内なら「最下部を見ている」とみなすか */
const BOTTOM_THRESHOLD_PX = 80;

/**
 * メッセージ一覧。スクロールは次のように振る舞う：
 * - 最下部を見ているとき、または自分が送信したときは、新着で最下部へ移動
 * - 上にスクロールして過去ログを読んでいるときは、新着が来ても位置を動かさない
 * - 過去ログを読み込んだときは、見ていた位置を保つ
 */
export function MessageList({
  messages,
  myUserId,
  hasMore,
  isLoadingOlder,
  onLoadOlder,
  onDelete,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const isAtBottomRef = useRef(true);
  const lastMessageIdRef = useRef<number | undefined>(undefined);
  // 過去ログ読み込み前のスクロール位置（読み込み後に同じ位置を見せるため）
  const prependAnchorRef = useRef<{ height: number; top: number } | null>(null);

  const scrollToBottom = () => {
    const el = containerRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  };

  useLayoutEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const anchor = prependAnchorRef.current;
    if (anchor) {
      el.scrollTop = anchor.top + (el.scrollHeight - anchor.height);
      prependAnchorRef.current = null;
      return;
    }

    const last = messages.at(-1);
    const hasNewMessage = last !== undefined && last.id !== lastMessageIdRef.current;
    lastMessageIdRef.current = last?.id;
    if (hasNewMessage && (isAtBottomRef.current || last.user.id === myUserId)) {
      scrollToBottom();
      isAtBottomRef.current = true;
    }
  }, [messages, myUserId]);

  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    isAtBottomRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < BOTTOM_THRESHOLD_PX;
  };

  // 画像は読み込み後に高さが決まるので、最下部を見ていたら追従する
  const handleImageLoad = () => {
    if (isAtBottomRef.current) scrollToBottom();
  };

  const handleLoadOlder = async () => {
    const el = containerRef.current;
    if (el) prependAnchorRef.current = { height: el.scrollHeight, top: el.scrollTop };
    await onLoadOlder();
  };

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto bg-[#8CABD9] px-3 py-4"
      aria-live="polite"
    >
      <div className="mx-auto flex max-w-3xl flex-col gap-3">
        {hasMore && (
          <button
            type="button"
            onClick={handleLoadOlder}
            disabled={isLoadingOlder}
            className="self-center rounded-full bg-black/20 px-4 py-1 text-xs text-white hover:bg-black/30 disabled:opacity-60"
          >
            {isLoadingOlder ? "読み込み中..." : "過去のメッセージを読み込む"}
          </button>
        )}

        {messages.length === 0 && (
          <p className="py-10 text-center text-sm text-white/90">
            まだメッセージはありません。最初のメッセージを送ってみましょう！
          </p>
        )}

        {messages.map((message, i) => {
          const prev = messages[i - 1];
          const isMine = message.user.id === myUserId;
          const notice = noticeText(message, myUserId);
          return (
            <Fragment key={message.id}>
              {(!prev || !isSameDay(prev.created_at, message.created_at)) && (
                <div className="self-center rounded-full bg-black/15 px-3 py-0.5 text-xs text-white">
                  {formatDate(message.created_at)}
                </div>
              )}
              {notice ? (
                <SystemNotice>{notice}</SystemNotice>
              ) : (
                <MessageBubble
                  message={message}
                  isMine={isMine}
                  onDelete={isMine ? onDelete : undefined}
                  onImageLoad={handleImageLoad}
                />
              )}
            </Fragment>
          );
        })}
      </div>
    </div>
  );
}
