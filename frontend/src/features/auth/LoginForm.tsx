"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { Button } from "@/components/Button";
import { ErrorMessage } from "@/components/ErrorMessage";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import { api } from "@/lib/api";
import { LIMITS } from "@/lib/config";
import { saveSession } from "@/lib/session";

import { useSession } from "./useSession";

/** ユーザー名で入室するフォーム。ログイン済みならトーク一覧へ移動する。 */
export function LoginForm() {
  const router = useRouter();
  const session = useSession();
  const [name, setName] = useState("");
  const { run, isPending, error } = useAsyncAction();
  const trimmed = name.trim();

  useEffect(() => {
    if (session) router.replace("/rooms");
  }, [session, router]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!trimmed || isPending) return;
    await run(async () => {
      const { token, user } = await api.login(trimmed);
      saveSession({ token, user }); // → 上の useEffect でトーク一覧へ
    }, "ログインに失敗しました");
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
          className="rounded-md border border-gray-300 px-3 py-2.5 outline-none focus:border-brand focus:ring-2 focus:ring-brand/30"
        />
        <span className="text-xs text-gray-500">
          {LIMITS.userName}文字以内。初めての名前なら自動で登録されます。
        </span>
      </label>

      <ErrorMessage message={error} />

      <Button
        type="submit"
        variant="primary"
        disabled={!trimmed || isPending}
        className="rounded-md py-2.5"
      >
        {isPending ? "入室中..." : "入室する"}
      </Button>
    </form>
  );
}
