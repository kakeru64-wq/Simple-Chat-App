import type { Metadata } from "next";

import { RoomsScreen } from "@/features/rooms/RoomsScreen";

export const metadata: Metadata = { title: "トーク | Simple Chat" };

export default function RoomsPage() {
  return <RoomsScreen />;
}
