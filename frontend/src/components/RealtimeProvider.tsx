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

import { WS_BASE_URL } from "@/lib/config";
import { clearSession } from "@/lib/session";
import type { RealtimeEvent, ServerEvent } from "@/lib/types";

export type ConnectionStatus = "connecting" | "open" | "closed";

type Listener = (event: RealtimeEvent) => void;

type RealtimeContextValue = {
  status: ConnectionStatus;
  subscribe: (listener: Listener) => () => void;
};

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

// バックエンド (app/routers/ws.py) と対応するクローズコード
const WS_CLOSE_UNAUTHORIZED = 4401;
const MAX_RECONNECT_DELAY_MS = 10_000;

/**
 * ログイン中ユーザー用の WebSocket 接続を 1 本だけ張り、受信イベントを購読者へ配る。
 * ルーム一覧（未読数・最新メッセージ）とチャット画面が同じ接続を共有する。
 * 切断時は指数バックオフで再接続し、接続のたびに "connection.opened" を流して
 * 購読者に取りこぼしの補完（REST での再取得）を促す。
 */
export function RealtimeProvider({ token, children }: { token: string; children: ReactNode }) {
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

      ws.onmessage = (e: MessageEvent<string>) => {
        emit(JSON.parse(e.data) as ServerEvent);
      };

      ws.onclose = (e) => {
        if (disposed) return;
        setStatus("closed");
        if (e.code === WS_CLOSE_UNAUTHORIZED) {
          clearSession(); // ガードによりログイン画面へ戻る
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

function useRealtimeContext(): RealtimeContextValue {
  const ctx = useContext(RealtimeContext);
  if (!ctx) throw new Error("RealtimeProvider が見つかりません");
  return ctx;
}

export function useConnectionStatus(): ConnectionStatus {
  return useRealtimeContext().status;
}

/** リアルタイムイベントを購読する。handler は常に最新の props/state を参照できる。 */
export function useRealtimeEvent(handler: (event: RealtimeEvent) => void): void {
  const { subscribe } = useRealtimeContext();
  const onEvent = useEffectEvent(handler);
  useEffect(() => subscribe((event) => onEvent(event)), [subscribe]);
}
