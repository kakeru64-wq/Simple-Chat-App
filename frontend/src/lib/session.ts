import type { Session } from "./types";

/**
 * ログイン情報（トークン + ユーザー）を localStorage に保存する小さなストア。
 * React からは useSyncExternalStore で購読する（hooks/useSession.ts）。
 */

const STORAGE_KEY = "chat.session";
const listeners = new Set<() => void>();

// getSnapshot は同じ値に対して同じ参照を返す必要があるため、生文字列単位でキャッシュする
let cachedRaw: string | null = null;
let cachedSession: Session | null = null;

function readStorage(): string | null {
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return null; // プライベートモード等で localStorage が使えない場合
  }
}

export function getSession(): Session | null {
  const raw = readStorage();
  if (raw !== cachedRaw) {
    cachedRaw = raw;
    try {
      cachedSession = raw ? (JSON.parse(raw) as Session) : null;
    } catch {
      cachedSession = null;
    }
  }
  return cachedSession;
}

export function saveSession(session: Session): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  } catch {
    // 保存できなくてもアプリは動かす（リロードでログアウトされるだけ）
  }
  notify();
}

export function clearSession(): void {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // noop
  }
  notify();
}

export function subscribeSession(listener: () => void): () => void {
  listeners.add(listener);
  // 他タブでのログイン/ログアウトにも追従する
  const onStorage = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY) listener();
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", onStorage);
  };
}

function notify(): void {
  listeners.forEach((l) => l());
}
