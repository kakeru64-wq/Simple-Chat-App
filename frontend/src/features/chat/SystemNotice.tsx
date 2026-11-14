import type { ReactNode } from "react";

/** トーク内の中央に出す小さな帯（システムメッセージ・取り消し済み） */
export function SystemNotice({ children }: { children: ReactNode }) {
  return (
    <p className="max-w-[90%] self-center rounded-full bg-black/15 px-3 py-0.5 text-center text-xs text-white">
      {children}
    </p>
  );
}
