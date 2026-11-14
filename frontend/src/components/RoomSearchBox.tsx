"use client";

import { LIMITS } from "@/lib/config";

type Props = {
  value: string;
  onChange: (value: string) => void;
};

/** ルーム名の検索欄 */
export function RoomSearchBox({ value, onChange }: Props) {
  return (
    <div className="relative">
      <svg
        aria-hidden
        viewBox="0 0 24 24"
        className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-gray-400"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
      >
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" />
      </svg>
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => e.key === "Escape" && onChange("")}
        maxLength={LIMITS.roomName}
        placeholder="ルーム名で検索"
        aria-label="ルーム名で検索"
        className="w-full rounded-full bg-gray-100 py-2 pr-9 pl-9 text-sm outline-none focus:ring-2 focus:ring-[#06C755]/30 [&::-webkit-search-cancel-button]:hidden"
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange("")}
          aria-label="検索をクリア"
          className="absolute top-1/2 right-2 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-full text-gray-400 hover:bg-gray-200 hover:text-gray-600"
        >
          ×
        </button>
      )}
    </div>
  );
}
