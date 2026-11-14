import { SessionGuard } from "@/features/auth/SessionGuard";
import { RealtimeProvider } from "@/features/realtime/RealtimeProvider";

/** /rooms 配下はログイン必須。WebSocket の接続は画面を移動しても共有する。 */
export default function RoomsLayout({ children }: LayoutProps<"/rooms">) {
  return (
    <SessionGuard>
      <RealtimeProvider>{children}</RealtimeProvider>
    </SessionGuard>
  );
}
