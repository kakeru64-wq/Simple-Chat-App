import type { ButtonHTMLAttributes } from "react";

const VARIANTS = {
  /** 緑の塗りボタン（主な操作） */
  primary: "bg-[#06C755] font-bold text-white hover:bg-[#05b14c]",
  /** 緑の枠線ボタン（参加など） */
  outline: "border border-[#06C755] font-bold text-[#06C755] hover:bg-[#06C755]/10",
  /** ヘッダー上の小さなボタン（ログアウト・退会など） */
  header: "shrink-0 rounded border border-white/40 px-2 py-1 text-xs hover:bg-white/10",
} as const;

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant: keyof typeof VARIANTS;
};

/**
 * 色と状態（ホバー・無効時の薄さ）だけを持つボタン。大きさ・角丸などは使う側が className で指定する。
 */
export function Button({ variant, className = "", type = "button", ...props }: Props) {
  return (
    <button
      type={type}
      className={`disabled:opacity-50 ${VARIANTS[variant]} ${className}`}
      {...props}
    />
  );
}
