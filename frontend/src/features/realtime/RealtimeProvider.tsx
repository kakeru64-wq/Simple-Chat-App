"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useEffectEvent,
  useRef,
  useState,
} from "react";

import { useAuthedSession } from "@/features/auth/SessionGuard";
import { WS_BASE_URL } from "@/lib/config";
import { clearSession } from "@/lib/session";
import type { RealtimeEvent, ServerEvent } from "@/lib/types";

export type ConnectionStatus = "connecting" | "open" | "closed";

type Listener = (event: RealtimeEvent) => void;

const RealtimeContext = createContext<{
  status: ConnectionStatus;
  subscribe: (listener: Listener) => () => void;
} | null>(null);

// バックエンド（app/api/routes/websocket.py）と対応するクローズコード
const WS_CLOSE_UNAUTHORIZED = 4401;
const MAX_RECONNECT_DELAY_MS = 10_000;

/**
 * ログイン中のユーザー用に WebSocket を 1 本だけ張り、届いたイベントを購読者へ配る。
 * トーク一覧とチャット画面は同じ接続を共有する（SessionGuard の内側で使う）。
 *
 * 切断されたら 1s, 2s, 4s… と間隔を空けて再接続し、接続するたびに
 * "connection.opened" を流して、購読者に取りこぼしの補完（REST での再取得）を促す。
 */
export function RealtimeProvider({ children }: { children: ReactNode }) {
  const { token } = useAuthedSession();
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const listenersRef = useRef(new Set<Listener>());

  const subscribe = useCallback((listener: Listener) => {
    listenersRef.current.add(listener);
    return () => {
      listenersRef.current.delete(listener);
    };
  }, []);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let attempt = 0;
    let disposed = false;
    const emit = (event: RealtimeEvent) => listenersRef.current.forEach((l) => l(event));

    const connect = () => {
      ws = new WebSocket(`${WS_BASE_URL}/ws?token=${encodeURIComponent(token)}`);
      ws.onopen = () => {
        attempt = 0;
        setStatus("open");
        emit({ type: "connection.opened" });
      };
      ws.onmessage = (e: MessageEvent<string>) => emit(JSON.parse(e.data) as ServerEvent);
      ws.onclose = (e) => {
        if (disposed) return;
        setStatus("closed");
        if (e.code === WS_CLOSE_UNAUTHORIZED) {
          clearSession(); // SessionGuard がログイン画面へ戻す
          return;
        }
        const delay = Math.min(1000 * 2 ** attempt, MAX_RECONNECT_DELAY_MS);
        attempt += 1;
        retryTimer = setTimeout(() => {
          setStatus("connecting");
          connect();
        }, delay);
      };
    };

    connect();
    return () => {
      disposed = true;
      clearTimeout(retryTimer);
      ws?.close();
    };
  }, [token]);

  return <RealtimeContext value={{ status, subscribe }}>{children}</RealtimeContext>;
}

function useRealtimeContext() {
  const ctx = useContext(RealtimeContext);
  if (!ctx) throw new Error("RealtimeProvider の内側で使ってください");
  return ctx;
}

/** WebSocket の接続状態 */
export function useConnectionStatus(): ConnectionStatus {
  return useRealtimeContext().status;
}

/** リアルタイムイベントを購読する。handler からは常に最新の props / state を参照できる。 */
export function useRealtimeEvent(handler: (event: RealtimeEvent) => void): void {
  const { subscribe } = useRealtimeContext();
  const onEvent = useEffectEvent(handler);
  useEffect(() => subscribe((event) => onEvent(event)), [subscribe]);
}
