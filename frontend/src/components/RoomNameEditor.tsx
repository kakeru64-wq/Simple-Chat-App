"use client";

import { type FormEvent, type KeyboardEvent, useState } from "react";

import { ApiError } from "@/lib/api";
import { LIMITS } from "@/lib/config";

type Props = {
  name: string;
  onRename: (name: string) => Promise<void>;
};

/** ヘッダーに置くトーク名。✎ でその場編集に切り替わる（Enter で保存、Esc で取り消し）。 */
export function RoomNameEditor({ name, onRename }: Props) {
  const [draft, setDraft] = useState<string | null>(null); // null = 表示モード
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cancel = () => {
    setDraft(null);
    setError(null);
  };

  const save = async (e?: FormEvent) => {
    e?.preventDefault();
    if (draft === null || isSaving) return;
    const trimmed = draft.trim();
    if (!trimmed) return;
    if (trimmed === name) return cancel();
    setIsSaving(true);
    setError(null);
    try {
      await onRename(trimmed);
      setDraft(null);
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 409
          ? "同じ名前のルームが既にあります"
          : err instanceof ApiError
            ? err.message
            : "変更に失敗しました",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.nativeEvent.isComposing || e.keyCode === 229) return; // IME 変換中は無視
    if (e.key === "Escape") cancel();
  };

  if (draft === null) {
    return (
      <span className="flex min-w-0 items-center gap-1">
        <span className="truncate">{name}</span>
        <button
          type="button"
          onClick={() => setDraft(name)}
          aria-label="トーク名を変更"
          title="トーク名を変更"
          className="shrink-0 rounded px-1 text-sm font-normal text-white/70 hover:bg-white/10 hover:text-white"
        >
          ✎
        </button>
      </span>
    );
  }

  return (
    <form onSubmit={save} className="relative flex min-w-0 flex-1 items-center gap-1">
      <input
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        maxLength={LIMITS.roomName}
        autoFocus
        aria-label="新しいトーク名"
        aria-invalid={error !== null}
        disabled={isSaving}
        className="min-w-0 flex-1 rounded bg-white px-2 py-1 text-sm font-normal text-gray-900 outline-none"
      />
      <button
        type="submit"
        disabled={isSaving || !draft.trim()}
        className="shrink-0 rounded bg-[#06C755] px-2 py-1 text-xs font-bold hover:bg-[#05b14c] disabled:opacity-50"
      >
        保存
      </button>
      <button
        type="button"
        onClick={cancel}
        disabled={isSaving}
        className="shrink-0 rounded px-2 py-1 text-xs font-normal hover:bg-white/10"
      >
        キャンセル
      </button>
      {error && (
        <p
          role="alert"
          className="absolute top-full left-0 z-10 mt-1 rounded bg-red-600 px-2 py-1 text-xs font-normal whitespace-nowrap text-white shadow"
        >
          {error}
        </p>
      )}
    </form>
  );
}
