"use client";

import { useRouter } from "next/navigation";
import { createContext, type ReactNode, useContext, useEffect } from "react";

import type { Session } from "@/lib/types";

import { useSession } from "./useSession";

const SessionContext = createContext<Session | null>(null);

/**
 * ログイン必須の画面を囲む。未ログインならログイン画面（/）へ戻し、
 * ログイン中なら子コンポーネントが useAuthedSession() でセッションを取得できるようにする。
 */
export function SessionGuard({ children }: { children: ReactNode }) {
  const session = useSession();
  const router = useRouter();

  useEffect(() => {
    if (session === null) router.replace("/");
  }, [session, router]);

  if (!session) return null; // 判定中、またはリダイレクト中
  return <SessionContext value={session}>{children}</SessionContext>;
}

/** SessionGuard の内側で、ログイン中のセッションを取得する。 */
export function useAuthedSession(): Session {
  const session = useContext(SessionContext);
  if (!session) throw new Error("useAuthedSession は SessionGuard の内側で使ってください");
  return session;
}
