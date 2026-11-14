import Link from "next/link";
import type { ReactNode } from "react";

import { AppHeader } from "@/components/AppHeader";

/** ヘッダー（戻る付き）＋ 中央寄せの本文。読み込み中・エラー・参加の案内などに使う。 */
export function CenteredScreen({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="flex h-dvh flex-col">
      <AppHeader title={title} backHref="/rooms" />
      <div className="flex flex-1 flex-col items-center justify-center gap-4 bg-gray-50 p-4 text-center text-gray-600">
        {children}
      </div>
    </div>
  );
}

export function BackToRoomsLink() {
  return (
    <Link href="/rooms" className="text-sm text-brand underline">
      トーク一覧へ戻る
    </Link>
  );
}
