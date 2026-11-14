import { Avatar } from "@/components/Avatar";
import { resolveMediaUrl } from "@/lib/api";
import { formatTime } from "@/lib/datetime";
import type { Message } from "@/lib/types";

type Props = {
  /** ユーザーの投稿（取り消されていないもの） */
  message: Message;
  isMine: boolean;
  /** 指定すると「取消」ボタンを出す（自分の投稿のみ） */
  onDelete?: (message: Message) => void;
  /** 画像の読み込み完了時（スクロール位置の調整用） */
  onImageLoad?: () => void;
};

/** LINE 風の吹き出し。自分は右・緑、他人は左・白で名前とアイコン付き。 */
export function MessageBubble({ message, isMine, onDelete, onImageLoad }: Props) {
  const body =
    message.kind === "image" && message.image_url ? (
      <a href={resolveMediaUrl(message.image_url)} target="_blank" rel="noopener noreferrer">
        {/* API サーバー上の任意サイズの画像なので、next/image ではなく img を使う */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={resolveMediaUrl(message.image_url)}
          alt={`${message.user.name}が送信した画像`}
          onLoad={onImageLoad}
          className="max-h-64 max-w-[60vw] rounded-2xl bg-white/40 object-contain sm:max-w-xs"
        />
      </a>
    ) : (
      <p
        className={`max-w-[70vw] rounded-2xl px-3 py-2 text-[15px] leading-relaxed break-words whitespace-pre-wrap sm:max-w-md ${
          isMine ? "rounded-tr-sm bg-bubble-mine" : "rounded-tl-sm bg-white"
        }`}
      >
        {message.content}
      </p>
    );

  const meta = (
    <div
      className={`flex shrink-0 flex-col justify-end gap-0.5 text-[10px] text-white/90 ${
        isMine ? "items-end" : "items-start"
      }`}
    >
      {onDelete && (
        <button
          type="button"
          onClick={() => onDelete(message)}
          // スマホでは常に表示、PC ではホバー・フォーカス時に表示
          className="rounded bg-black/20 px-1.5 py-0.5 text-white hover:bg-black/40 focus:opacity-100 sm:opacity-0 sm:group-hover:opacity-100"
        >
          取消
        </button>
      )}
      <time dateTime={message.created_at}>{formatTime(message.created_at)}</time>
    </div>
  );

  if (isMine) {
    return (
      <div className="group flex justify-end gap-1.5">
        {meta}
        {body}
      </div>
    );
  }
  return (
    <div className="flex gap-2">
      <Avatar name={message.user.name} userId={message.user.id} />
      <div className="flex min-w-0 flex-col gap-1">
        <span className="text-xs text-white">{message.user.name}</span>
        <div className="flex gap-1.5">
          {body}
          {meta}
        </div>
      </div>
    </div>
  );
}
