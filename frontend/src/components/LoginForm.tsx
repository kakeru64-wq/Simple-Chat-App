"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { useSession } from "@/hooks/useSession";
import { ApiError, api } from "@/lib/api";
import { LIMITS } from "@/lib/config";
import { saveSession } from "@/lib/session";

export function LoginForm() {
  const router = useRouter();
  const session = useSession();
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // ログイン済みならルーム一覧へ
  useEffect(() => {
    if (session) router.replace("/rooms");
  }, [session, router]);

  const trimmed = name.trim();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!trimmed || isSubmitting) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const res = await api.login(trimmed);
      saveSession({ token: res.token, user: res.user }); // → effect でリダイレクト
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "ログインに失敗しました");
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex w-full flex-col gap-4">
      <label className="flex flex-col gap-2">
        <span className="text-sm font-bold text-gray-700">ユーザー名</span>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={LIMITS.userName}
          placeholder="例：taro"
          autoFocus
          autoComplete="username"
          className="rounded-md border border-gray-300 px-3 py-2.5 outline-none focus:border-[#06C755] focus:ring-2 focus:ring-[#06C755]/30"
        />
        <span className="text-xs text-gray-500">
          {LIMITS.userName}文字以内。初めての名前なら自動で登録されます。
        </span>
      </label>

      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={!trimmed || isSubmitting}
        className="rounded-md bg-[#06C755] py-2.5 font-bold text-white transition hover:bg-[#05b14c] disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isSubmitting ? "入室中..." : "入室する"}
      </button>
    </form>
  );
}
