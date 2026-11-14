"use client";

import { useSyncExternalStore } from "react";

import { getSession, subscribeSession } from "@/lib/session";
import type { Session } from "@/lib/types";

/**
 * 現在のログイン情報（localStorage）を返し、変化を購読する。
 * - undefined : サーバー描画中・ハイドレーション前（まだ分からない）
 * - null      : 未ログイン
 */
export function useSession(): Session | null | undefined {
  return useSyncExternalStore(subscribeSession, getSession, () => undefined);
}
