"use client";

import { type FormEvent, type KeyboardEvent, useRef, useState } from "react";

import { ApiError } from "@/lib/api";
import { LIMITS } from "@/lib/config";

type Props = {
  onSend: (content: string) => Promise<void>;
  disabled?: boolean;
};

/**
 * メッセージ送信フォーム。
 * Enter で送信、Shift+Enter で改行。日本語入力の変換確定の Enter では送信しない。
 */
export function MessageInput({ onSend, disabled = false }: Props) {
  const [content, setContent] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const trimmed = content.trim();
  const canSend = trimmed.length > 0 && !isSending && !disabled;

  const submit = async () => {
    if (!canSend) return;
    setIsSending(true);
    setError(null);
    try {
      await onSend(trimmed);
      setContent("");
    } catch (err) {
      // 失敗時は入力内容を残して再送できるようにする
      setError(err instanceof ApiError ? err.message : "送信に失敗しました");
    } finally {
      setIsSending(false);
      textareaRef.current?.focus();
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    void submit();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // isComposing: IME 変換中（keyCode 229 は一部ブラウザ向けのフォールバック）
    if (e.nativeEvent.isComposing || e.keyCode === 229) return;
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void submit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="shrink-0 border-t border-gray-200 bg-white px-3 py-2">
      {error && (
        <p role="alert" className="mx-auto max-w-3xl pb-1 text-xs text-red-600">
          {error}
        </p>
      )}
      <div className="mx-auto flex max-w-3xl items-end gap-2">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          maxLength={LIMITS.message}
          rows={1}
          placeholder="メッセージを入力（Shift+Enterで改行）"
          aria-label="メッセージ"
          className="field-sizing-content max-h-32 min-h-10 flex-1 resize-none rounded-2xl bg-gray-100 px-4 py-2 outline-none focus:ring-2 focus:ring-[#06C755]/30"
        />
        <button
          type="submit"
          disabled={!canSend}
          className="h-10 shrink-0 rounded-full bg-[#06C755] px-4 text-sm font-bold text-white hover:bg-[#05b14c] disabled:cursor-not-allowed disabled:opacity-40"
        >
          送信
        </button>
      </div>
    </form>
  );
}
