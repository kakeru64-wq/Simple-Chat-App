"use client";

import { useRouter } from "next/navigation";
import { useEffect, useSyncExternalStore } from "react";

import { getSession, subscribeSession } from "@/lib/session";
import type { Session } from "@/lib/types";

/**
 * 現在のログイン情報を返す。
 * - `undefined`: サーバー描画中/ハイドレーション前（まだ分からない）
 * - `null`: 未ログイン
 */
export function useSession(): Session | null | undefined {
  return useSyncExternalStore(subscribeSession, getSession, () => undefined);
}

/** ログイン必須の画面で使う。未ログインならログイン画面へリダイレクトする。 */
export function useRequireSession(): Session | null | undefined {
  const session = useSession();
  const router = useRouter();

  useEffect(() => {
    if (session === null) router.replace("/");
  }, [session, router]);

  return session;
}
