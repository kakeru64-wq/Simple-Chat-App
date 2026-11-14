import { Avatar } from "@/components/Avatar";
import { formatTime } from "@/lib/format";
import type { Message } from "@/lib/types";

type Props = {
  message: Message;
  isMine: boolean;
};

/** LINE 風の吹き出し。自分は右・緑、他人は左・白＋名前とアイコン。 */
export function MessageBubble({ message, isMine }: Props) {
  const time = (
    <time dateTime={message.created_at} className="shrink-0 self-end text-[10px] text-white/90">
      {formatTime(message.created_at)}
    </time>
  );
  const bubble = (
    <p
      className={`max-w-[70vw] whitespace-pre-wrap break-words rounded-2xl px-3 py-2 text-[15px] leading-relaxed sm:max-w-md ${
        isMine ? "rounded-tr-sm bg-[#8DE055]" : "rounded-tl-sm bg-white"
      }`}
    >
      {message.content}
    </p>
  );

  if (isMine) {
    return (
      <div className="flex justify-end gap-1.5">
        {time}
        {bubble}
      </div>
    );
  }

  return (
    <div className="flex gap-2">
      <Avatar name={message.user.name} userId={message.user.id} />
      <div className="flex min-w-0 flex-col gap-1">
        <span className="text-xs text-white">{message.user.name}</span>
        <div className="flex gap-1.5">
          {bubble}
          {time}
        </div>
      </div>
    </div>
  );
}
