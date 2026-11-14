import type { Metadata } from "next";

import { RoomsView } from "@/components/RoomsView";

export const metadata: Metadata = { title: "ルーム一覧 | Simple Chat" };

export default function RoomsPage() {
  return <RoomsView />;
}
