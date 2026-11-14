import { API_BASE_URL } from "@/lib/config";
import { clearSession, getSession } from "@/lib/session";

/** API がエラーを返した（または接続できなかった）ことを表す。message は画面に出せる日本語。 */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** 画面に表示するエラー文。ApiError ならその内容、それ以外は fallback。 */
export function getErrorMessage(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

/** API が返す相対パス（/uploads/...）を、ブラウザで開ける URL にする */
export function resolveMediaUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  /** JSON にするオブジェクト、または画像アップロード用の FormData */
  body?: unknown;
  /** false なら Authorization ヘッダーを付けない（ログイン時） */
  auth?: boolean;
};

/** API を呼び出し、JSON を型付きで返す。失敗時は ApiError を投げる。 */
export async function request<T>(
  path: string,
  { method = "GET", body, auth = true }: RequestOptions = {},
): Promise<T> {
  const isForm = body instanceof FormData;
  const headers: Record<string, string> = {};
  // FormData のときは boundary 付きの Content-Type をブラウザに付けさせる
  if (body !== undefined && !isForm) headers["Content-Type"] = "application/json";
  const token = auth ? getSession()?.token : undefined;
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "サーバーに接続できませんでした");
  }

  if (res.status === 401 && auth) {
    // トークンが無効：ログイン情報を消すと、SessionGuard がログイン画面へ戻す
    clearSession();
  }
  if (!res.ok) throw new ApiError(res.status, await errorMessageOf(res));
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** ステータスごとの、利用者向けのエラー文 */
const STATUS_MESSAGES: Record<number, string> = {
  403: "この操作を行う権限がありません",
  404: "見つかりませんでした",
  409: "同じ名前のルームが既にあります",
  413: "ファイルサイズが大きすぎます（5MBまで）",
  415: "対応していないファイル形式です（JPEG / PNG / GIF / WebP）",
};

async function errorMessageOf(res: Response): Promise<string> {
  if (STATUS_MESSAGES[res.status]) return STATUS_MESSAGES[res.status];
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    // FastAPI の入力チェックエラーは配列で返る
    if (Array.isArray(data.detail) && data.detail[0]?.msg) return data.detail[0].msg;
  } catch {
    // JSON でないレスポンス
  }
  return `エラーが発生しました (${res.status})`;
}
