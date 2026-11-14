"use client";

import { createContext, type ReactNode, useContext } from "react";

import { RealtimeProvider } from "@/components/RealtimeProvider";
import { useRequireSession } from "@/hooks/useSession";
import type { Session } from "@/lib/types";

const SessionContext = createContext<Session | null>(null);

/**
 * ログイン必須画面の共通の枠。
 * 未ログインならログイン画面へ戻し、ログイン中なら WebSocket 接続とセッションを子に提供する。
 */
export function AuthenticatedShell({ children }: { children: ReactNode }) {
  const session = useRequireSession();
  if (!session) return null; // 判定中 or リダイレクト中

  return (
    <SessionContext value={session}>
      <RealtimeProvider token={session.token}>{children}</RealtimeProvider>
    </SessionContext>
  );
}

/** AuthenticatedShell の内側で、ログイン中のセッションを取得する。 */
export function useAuthedSession(): Session {
  const session = useContext(SessionContext);
  if (!session) throw new Error("AuthenticatedShell の外側で呼ばれました");
  return session;
}
