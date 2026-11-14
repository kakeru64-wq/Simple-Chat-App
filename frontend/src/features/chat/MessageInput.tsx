"use client";

import { type ChangeEvent, type FormEvent, type KeyboardEvent, useRef, useState } from "react";

import { Button } from "@/components/Button";
import { ErrorMessage } from "@/components/ErrorMessage";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import { ACCEPTED_IMAGE_TYPES, LIMITS } from "@/lib/config";
import { isImeComposing } from "@/lib/keyboard";

type Props = {
  onSendText: (content: string) => Promise<void>;
  onSendImage: (file: File) => Promise<void>;
  disabled?: boolean;
};

/**
 * 送信フォーム（テキスト・画像）。
 * Enter で送信、Shift+Enter で改行。日本語入力の変換を確定する Enter では送信しない。
 */
export function MessageInput({ onSendText, onSendImage, disabled = false }: Props) {
  const [content, setContent] = useState("");
  const { run, isPending, error, setError } = useAsyncAction();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const trimmed = content.trim();
  const isBusy = isPending || disabled;

  const sendText = async () => {
    if (!trimmed || isBusy) return;
    // 失敗したときは入力内容を残し、そのまま再送できるようにする
    if (await run(() => onSendText(trimmed), "送信に失敗しました")) setContent("");
    textareaRef.current?.focus();
  };

  const sendImage = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // 同じファイルを続けて選べるようにリセット
    if (!file) return;
    // サーバーでも検証するが、明らかな誤りは送る前に知らせる
    if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
      return setError("対応していないファイル形式です（JPEG / PNG / GIF / WebP）");
    }
    if (file.size > LIMITS.imageBytes) {
      return setError("ファイルサイズが大きすぎます（5MBまで）");
    }
    await run(() => onSendImage(file), "画像の送信に失敗しました");
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    void sendText();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (isImeComposing(e)) return;
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendText();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="shrink-0 border-t border-gray-200 bg-white px-3 py-2">
      <ErrorMessage message={error} className="mx-auto max-w-3xl pb-1 text-xs" />
      <div className="mx-auto flex max-w-3xl items-end gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_IMAGE_TYPES.join(",")}
          onChange={sendImage}
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
          <ImageIcon />
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
          className="field-sizing-content max-h-32 min-h-10 flex-1 resize-none rounded-2xl bg-gray-100 px-4 py-2 outline-none focus:ring-2 focus:ring-brand/30"
        />
        <Button
          type="submit"
          variant="primary"
          disabled={!trimmed || isBusy}
          className="h-10 rounded-full px-4 text-sm"
        >
          {isPending ? "送信中" : "送信"}
        </Button>
      </div>
    </form>
  );
}

function ImageIcon() {
  return (
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
  );
}
