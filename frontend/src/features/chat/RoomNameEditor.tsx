"use client";

import { type FormEvent, type KeyboardEvent, useState } from "react";

import { Button } from "@/components/Button";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import { LIMITS } from "@/lib/config";
import { isImeComposing } from "@/lib/keyboard";

type Props = {
  name: string;
  /** 新しい名前を保存する。失敗時は例外を投げる（エラー文はこの部品が表示する） */
  onRename: (name: string) => Promise<void>;
};

/** ヘッダーのトーク名。✎ でその場の編集に切り替わる（Enter で保存、Esc でキャンセル）。 */
export function RoomNameEditor({ name, onRename }: Props) {
  const [draft, setDraft] = useState<string | null>(null); // null = 表示モード
  const { run, isPending, error, setError } = useAsyncAction();

  const cancel = () => {
    setDraft(null);
    setError(null);
  };

  const save = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = draft?.trim();
    if (!trimmed || isPending) return;
    if (trimmed === name) return cancel();
    if (await run(() => onRename(trimmed), "変更に失敗しました")) setDraft(null);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!isImeComposing(e) && e.key === "Escape") cancel();
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
        disabled={isPending}
        className="min-w-0 flex-1 rounded bg-white px-2 py-1 text-sm font-normal text-gray-900 outline-none"
      />
      <Button
        type="submit"
        variant="primary"
        disabled={isPending || !draft.trim()}
        className="rounded px-2 py-1 text-xs"
      >
        保存
      </Button>
      <button
        type="button"
        onClick={cancel}
        disabled={isPending}
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
