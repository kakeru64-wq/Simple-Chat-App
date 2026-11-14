import { LoginForm } from "@/components/LoginForm";

/** ログイン画面 */
export default function LoginPage() {
  return (
    <main className="flex flex-1 items-center justify-center bg-[#273246] p-4">
      <div className="flex w-full max-w-sm flex-col items-center gap-6 rounded-2xl bg-white p-8 shadow-xl">
        <div className="flex flex-col items-center gap-2">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#06C755] text-2xl font-bold text-white">
            💬
          </div>
          <h1 className="text-xl font-bold">Simple Chat</h1>
          <p className="text-sm text-gray-500">ユーザー名を入力して入室してください</p>
        </div>
        <LoginForm />
      </div>
    </main>
  );
}
