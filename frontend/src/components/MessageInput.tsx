"use client";

import { type ChangeEvent, type FormEvent, type KeyboardEvent, useRef, useState } from "react";

import { ApiError } from "@/lib/api";
import { ACCEPTED_IMAGE_TYPES, LIMITS } from "@/lib/config";

type Props = {
  onSend: (content: string) => Promise<void>;
  onSendImage: (file: File) => Promise<void>;
  disabled?: boolean;
};

/**
 * メッセージ送信フォーム（テキスト・画像）。
 * Enter で送信、Shift+Enter で改行。日本語入力の変換確定の Enter では送信しない。
 */
export function MessageInput({ onSend, onSendImage, disabled = false }: Props) {
  const [content, setContent] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const trimmed = content.trim();
  const isBusy = isSending || disabled;

  /** 送信処理の共通部分：二重送信防止とエラー表示 */
  const run = async (action: () => Promise<void>, fallbackError: string) => {
    setIsSending(true);
    setError(null);
    try {
      await action();
      return true;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : fallbackError);
      return false;
    } finally {
      setIsSending(false);
      textareaRef.current?.focus();
    }
  };

  const submitText = async () => {
    if (!trimmed || isBusy) return;
    // 失敗時は入力内容を残して再送できるようにする
    if (await run(() => onSend(trimmed), "送信に失敗しました")) setContent("");
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    void submitText();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // isComposing: IME 変換中（keyCode 229 は一部ブラウザ向けのフォールバック）
    if (e.nativeEvent.isComposing || e.keyCode === 229) return;
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void submitText();
    }
  };

  const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // 同じファイルを続けて選べるようにリセット
    if (!file) return;
    // サーバーでも検証するが、明らかな誤りは送信前に知らせる
    if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
      setError("対応していないファイル形式です（JPEG / PNG / GIF / WebP）");
      return;
    }
    if (file.size > LIMITS.imageBytes) {
      setError("ファイルサイズが大きすぎます（5MBまで）");
      return;
    }
    await run(() => onSendImage(file), "画像の送信に失敗しました");
  };

  return (
    <form onSubmit={handleSubmit} className="shrink-0 border-t border-gray-200 bg-white px-3 py-2">
      {error && (
        <p role="alert" className="mx-auto max-w-3xl pb-1 text-xs text-red-600">
          {error}
        </p>
      )}
      <div className="mx-auto flex max-w-3xl items-end gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_IMAGE_TYPES.join(",")}
          onChange={handleFileChange}
          className="hidden"
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isBusy}
          aria-label="画像を送信"
          title="画像を送信"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-gray-500 hover:bg-gray-100 disabled:opacity-40"
        >
          <svg
            viewBox="0 0 24 24"
            className="h-6 w-6"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.8}
          >
            <rect x="3" y="5" width="18" height="14" rx="2" />
            <circle cx="8.5" cy="10" r="1.5" />
            <path d="m21 16-5-5-8 8" />
          </svg>
        </button>
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
          disabled={!trimmed || isBusy}
          className="h-10 shrink-0 rounded-full bg-[#06C755] px-4 text-sm font-bold text-white hover:bg-[#05b14c] disabled:cursor-not-allowed disabled:opacity-40"
        >
          {isSending ? "送信中" : "送信"}
        </button>
      </div>
    </form>
  );
}
