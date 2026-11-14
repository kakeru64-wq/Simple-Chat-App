import { AuthenticatedShell } from "@/components/AuthenticatedShell";

/** /rooms 配下はログイン必須。WebSocket 接続は画面遷移をまたいで共有する。 */
export default function RoomsLayout({ children }: LayoutProps<"/rooms">) {
  return <AuthenticatedShell>{children}</AuthenticatedShell>;
}
