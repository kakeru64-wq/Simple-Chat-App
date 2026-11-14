"use client";

import { useCallback, useState } from "react";

import { getErrorMessage } from "@/lib/api";

/**
 * ボタン操作などの非同期処理に共通する「実行中」と「エラー表示」をまとめたフック。
 *
 * const { run, isPending, error } = useAsyncAction();
 * const ok = await run(() => api.createRoom(name), "ルームの作成に失敗しました");
 */
export function useAsyncAction() {
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /** action を実行する。成功なら true、失敗ならエラー文をセットして false を返す。 */
  const run = useCallback(async (action: () => Promise<unknown>, fallbackError: string) => {
    setIsPending(true);
    setError(null);
    try {
      await action();
      return true;
    } catch (e) {
      setError(getErrorMessage(e, fallbackError));
      return false;
    } finally {
      setIsPending(false);
    }
  }, []);

  return { run, isPending, error, setError };
}
