import type { NextConfig } from "next";
import path from "path";
import { fileURLToPath } from "url";

/** 与 next.config 同目录 = 真正的应用根（勿依赖 process.cwd，避免在 Desktop 等父目录里跑 dev 时解析错） */
const appRoot = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  turbopack: {
    root: appRoot,
    resolveAlias: {
      tailwindcss: path.join(appRoot, "node_modules", "tailwindcss"),
      "tw-animate-css": path.join(
        appRoot,
        "node_modules",
        "tw-animate-css",
        "dist",
        "tw-animate.css",
      ),
      "shadcn/tailwind.css": path.join(
        appRoot,
        "node_modules",
        "shadcn",
        "dist",
        "tailwind.css",
      ),
    },
  },
  webpack: (config) => {
    config.resolve = config.resolve ?? {};
    config.resolve.alias = {
      ...config.resolve.alias,
      tailwindcss: path.join(appRoot, "node_modules", "tailwindcss"),
      "tw-animate-css": path.join(
        appRoot,
        "node_modules",
        "tw-animate-css",
        "dist",
        "tw-animate.css",
      ),
      "shadcn/tailwind.css": path.join(
        appRoot,
        "node_modules",
        "shadcn",
        "dist",
        "tailwind.css",
      ),
    };
    return config;
  },
  async headers() {
    return [
      {
        source: "/godot/:file*\\.data\\.gz",
        headers: [
          { key: "Content-Type", value: "application/octet-stream" },
          { key: "Content-Encoding", value: "gzip" },
          { key: "Cache-Control", value: "public, max-age=31536000, immutable" },
        ],
      },
      {
        source: "/godot/:file*\\.js\\.gz",
        headers: [
          { key: "Content-Type", value: "application/javascript; charset=utf-8" },
          { key: "Content-Encoding", value: "gzip" },
          { key: "Cache-Control", value: "public, max-age=31536000, immutable" },
        ],
      },
      {
        source: "/godot/:file*\\.wasm\\.gz",
        headers: [
          { key: "Content-Type", value: "application/wasm" },
          { key: "Content-Encoding", value: "gzip" },
          { key: "Cache-Control", value: "public, max-age=31536000, immutable" },
        ],
      },
    ];
  },
  // ===== 新增代码 START =====
  // 与 .env.local 中 NEXT_PUBLIC_API_URL 对齐：将遗留 /api/proxy 请求转发到同一后端
  async rewrites() {
    const root = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");
    if (!root) return [];
    return [
      {
        source: "/api/proxy/:path*",
        destination: `${root}/api/v1/:path*`,
      },
    ];
  },
  // ===== 新增代码 END =====
};

export default nextConfig;
