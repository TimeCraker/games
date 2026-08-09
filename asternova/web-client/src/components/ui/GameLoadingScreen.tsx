"use client"

import * as React from "react"
import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

/**
 * 统一加载屏（Stage A 共享组件）
 * 复用 app/arena/page.tsx:276-310 的玻璃卡 + 进度条工艺 + star-chart-grid + 品牌字
 * 替换 4 处裸 loading（各 PageClient 的 loading 回调 + arena 加载序列）
 *
 * progress 提供 → 真进度条（arena 工艺）；未提供 → 旋转 spinner（indeterminate）
 */
export function GameLoadingScreen({
  label = "正在进入战场",
  progress,
  hint = "建议保持当前页面，加载完成后将自动开始",
  className,
}: {
  label?: string
  progress?: number
  hint?: string
  className?: string
}) {
  const pct = typeof progress === "number" ? Math.max(0, Math.min(100, progress)) : null
  const hasProgress = pct !== null
  return (
    <div
      className={cn(
        "relative flex h-full min-h-[100dvh] w-full items-center justify-center overflow-hidden bg-space-black text-white",
        className,
      )}
    >
      <div className="star-chart-grid pointer-events-none absolute inset-0 opacity-40" />
      <div className="relative z-10 w-full max-w-md rounded-[28px] border border-white/20 bg-[linear-gradient(155deg,rgba(255,255,255,0.16),rgba(255,255,255,0.03))] p-8 text-center shadow-lg backdrop-blur-glass-lg">
        <span className="font-display text-xs tracking-[0.38em] text-white/55">PREPARING</span>
        <h2 className="mt-3 font-display text-xl font-bold tracking-wider text-white">{label}</h2>

        <div className="mt-6 flex items-center justify-center">
          {hasProgress ? (
            <div className="h-2.5 w-full overflow-hidden rounded-full border border-white/20 bg-white/10">
              <div
                className="h-full rounded-full bg-[linear-gradient(90deg,rgba(255,255,255,0.85),rgba(167,243,208,0.92),rgba(147,197,253,0.9))] shadow-glow-cyan transition-[width] duration-300"
                style={{ width: `${pct}%` }}
              />
            </div>
          ) : (
            <Loader2 className="h-7 w-7 animate-spin text-brand-violet/80" />
          )}
        </div>

        {hasProgress && (
          <p className="mt-2 font-mono-data text-[11px] tracking-[0.12em] text-white/45">{Math.round(pct)}%</p>
        )}
        {hint && (
          <p className="mt-5 font-mono-data text-[11px] leading-relaxed tracking-[0.08em] text-white/40">{hint}</p>
        )}
      </div>
    </div>
  )
}
