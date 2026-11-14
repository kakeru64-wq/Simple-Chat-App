import type { ButtonHTMLAttributes } from "react";

const VARIANTS = {
  /** 緑の塗りボタン（主な操作） */
  primary: "bg-brand font-bold text-white hover:bg-brand-dark",
  /** 緑の枠線ボタン（参加など） */
  outline: "border border-brand font-bold text-brand hover:bg-brand/10",
  /** ヘッダー上の小さなボタン（ログアウト・退会など） */
  header: "rounded border border-white/40 px-2 py-1 text-xs hover:bg-white/10",
} as const;

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant: keyof typeof VARIANTS;
};

/**
 * 色と状態（ホバー・無効）だけを持つボタン。大きさと角丸は使う側が className で指定する。
 */
export function Button({ variant, className = "", type = "button", ...props }: Props) {
  return (
    <button
      type={type}
      className={`shrink-0 transition disabled:cursor-not-allowed disabled:opacity-50 ${VARIANTS[variant]} ${className}`}
      {...props}
    />
  );
}
