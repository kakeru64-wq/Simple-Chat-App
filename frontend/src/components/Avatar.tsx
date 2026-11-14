const COLORS = ["bg-sky-500", "bg-amber-500", "bg-rose-500", "bg-violet-500", "bg-teal-500"];

/** ユーザー名の頭文字を表示する丸アイコン。色はユーザー ID から決める。 */
export function Avatar({ name, userId }: { name: string; userId: number }) {
  const color = COLORS[userId % COLORS.length];
  return (
    <div
      aria-hidden
      className={`${color} flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white`}
    >
      {name.slice(0, 1).toUpperCase()}
    </div>
  );
}
