import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // cacheComponents は使用しない：本アプリは画面をクライアント側で描画するため不要であり、
  // 有効にすると日本語などを含むパスで `next dev` の動的ルートが 500 になる問題があるため。
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
