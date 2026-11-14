"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { Button } from "@/components/Button";
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

/** 画面上部の紺色のヘッダー */
export function AppHeader({ title, backHref, userName, actions }: Props) {
  const logout = async () => {
    await api.logout().catch(() => {}); // サーバー側の失敗に関わらずローカルの情報は消す
    clearSession(); // SessionGuard がログイン画面へ戻す
  };

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 bg-header px-4 text-white">
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
          <Button variant="header" onClick={logout}>
            ログアウト
          </Button>
        </div>
      )}
    </header>
  );
}
