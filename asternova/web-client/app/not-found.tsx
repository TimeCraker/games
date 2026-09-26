import Link from "next/link"
import { ChevronRight } from "lucide-react"
import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "404 星际失联",
  description: "你寻找的坐标不存在于星图之中",
}

/**
 * 品牌 404：深空风格 + 返回大厅入口。
 * 原站点无 not-found（落 Next 默认灰页，与产品风格割裂）。
 * 纯静态、无 client、无动态依赖。
 */
export default function NotFoundPage() {
  return (
    <main id="main-content" tabIndex={-1} className="relative flex min-h-[100dvh] flex-col items-center justify-center overflow-hidden bg-space-black px-6 text-center text-white">
      {/* 星图网格 */}
      <div className="star-chart-grid pointer-events-none absolute inset-0 z-0" aria-hidden="true" />
      {/* 紫色星云光晕 */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute left-1/2 top-1/2 z-0 h-[420px] w-[420px] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-25 blur-[90px]"
        style={{ background: "radial-gradient(circle at 50% 50%, rgba(139,92,246,0.55), transparent 70%)" }}
      />
      <div className="relative z-10">
        <p className="font-mono-data text-[12px] uppercase tracking-[0.4em] text-white/50">SIGNAL LOST</p>
        <h1 className="mt-5 font-orbitron text-6xl font-black tracking-[0.06em] text-white sm:text-7xl">
          4<span className="text-hud-accent">0</span>4
        </h1>
        <p className="mt-4 max-w-sm text-sm leading-relaxed text-white/50">
          你寻找的坐标不存在于星图之中。它可能已陨落、漂移，或从未存在。
        </p>
        <Link
          href="/lobby"
          className="mt-9 inline-flex min-h-11 items-center gap-2 rounded-full border border-glass-border bg-glass-bg px-6 py-2.5 text-sm font-medium text-white/90 backdrop-blur-glass-md transition-colors hover:bg-white/10 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-hud-accent/60 focus-visible:ring-offset-2 focus-visible:ring-offset-space-black"
        >
          返回游戏大厅
          <ChevronRight className="h-4 w-4" strokeWidth={2} aria-hidden="true" />
        </Link>
      </div>
    </main>
  )
}
