"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { api } from "@/lib/api";
import { clearSession } from "@/lib/session";

type Props = {
  title: ReactNode;
  /** 指定すると左側に「戻る」リンクを表示する */
  backHref?: string;
  /** 指定するとユーザー名とログアウトボタンを表示する */
  userName?: string;
  /** 右側に置く追加の操作 */
  actions?: ReactNode;
};

export function AppHeader({ title, backHref, userName, actions }: Props) {
  const logout = async () => {
    try {
      await api.logout();
    } catch {
      // サーバー側の失敗に関わらずローカルのログイン情報は消す
    }
    clearSession(); // ガードがログイン画面へ戻す
  };

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 bg-[#273246] px-4 text-white">
      {backHref && (
        <Link href={backHref} aria-label="戻る" className="-ml-1 px-1 text-2xl leading-none">
          ‹
        </Link>
      )}
      <h1 className="min-w-0 flex-1 truncate text-base font-bold">{title}</h1>
      {actions}
      {userName && (
        <div className="flex items-center gap-3 text-sm">
          <span className="max-w-32 truncate text-white/80">{userName}</span>
          <button type="button" onClick={logout} className={headerButtonClass}>
            ログアウト
          </button>
        </div>
      )}
    </header>
  );
}

export const headerButtonClass =
  "shrink-0 rounded border border-white/40 px-2 py-1 text-xs hover:bg-white/10 disabled:opacity-50";
