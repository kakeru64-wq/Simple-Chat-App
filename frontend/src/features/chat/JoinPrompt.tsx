"use client";

import { Button } from "@/components/Button";
import { BackToRoomsLink, CenteredScreen } from "@/components/CenteredScreen";
import { ErrorMessage } from "@/components/ErrorMessage";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import { api } from "@/lib/api";
import type { Room } from "@/lib/types";

/** 参加していないルームを開いたときの案内（URL を直接開いた場合など） */
export function JoinPrompt({ room, onJoined }: { room: Room; onJoined: (room: Room) => void }) {
  const { run, isPending, error } = useAsyncAction();

  const join = () => run(async () => onJoined(await api.joinRoom(room.id)), "参加に失敗しました");

  return (
    <CenteredScreen title={room.name}>
      <p className="text-lg font-bold text-gray-800">{room.name}</p>
      <p className="text-sm">{room.member_count}人が参加中</p>
      <Button
        variant="primary"
        onClick={join}
        disabled={isPending}
        className="rounded-md px-8 py-2.5"
      >
        {isPending ? "参加中..." : "参加する"}
      </Button>
      <ErrorMessage message={error} />
      <BackToRoomsLink />
    </CenteredScreen>
  );
}
