"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

/**
 * 统一液体进度条（Stage A 共享组件）
 * 提炼 ArenaHud skew + WAVE_MASK 工艺与 nebula-survivor 的 inset 高光
 * 替换 3 套独立进度条：ArenaHud HpBar/EnergyBar、nebula HP/XP、nova-ball progressTrack
 */
const WAVE_MASK =
  'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 1200 120\' preserveAspectRatio=\'none\'%3E%3Cpath d=\'M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V120H282.65C297.82,95.68,307.39,73.19,321.39,56.44Z\' style=\'fill:%23000;\'%3E%3C/path%3E%3C/svg%3E")'

type LiquidVariant = "hp" | "energy" | "xp" | "progress"

const VARIANT_CFG: Record<
  LiquidVariant,
  { height: string; track: string; fill: string; defaultSkew: boolean }
> = {
  hp: {
    height: "h-7",
    track: "border-white/30",
    fill: "bg-gradient-to-r from-fuchsia-300 via-pink-500 to-violet-900",
    defaultSkew: true,
  },
  energy: {
    height: "h-3",
    track: "border-white/20",
    fill: "bg-gradient-to-r from-yellow-400 to-cyan-400",
    defaultSkew: true,
  },
  xp: {
    height: "h-2",
    track: "border-emerald-950/40",
    fill: "bg-gradient-to-b from-[#b8ffd9] via-[#34d399] to-[#065f46]",
    defaultSkew: false,
  },
  progress: {
    height: "h-3.5",
    track: "border-white/14",
    fill: "bg-gradient-to-r from-pink-300 via-purple-400 to-indigo-400",
    defaultSkew: false,
  },
}

export function LiquidBar({
  value,
  max,
  variant,
  side = "left",
  skew,
  wave = false,
  showHighlight = true,
  success = false,
  className,
}: {
  value: number
  max: number
  variant: LiquidVariant
  side?: "left" | "right"
  /** 默认 hp/energy 启用 skew（ArenaHud 风格），xp/progress 不 skew */
  skew?: boolean
  /** 顶部波纹遮罩（WAVE_MASK），默认 false */
  wave?: boolean
  /** inset 顶部高光线，默认 true（nebula 风格） */
  showHighlight?: boolean
  /** 满/达标态：fill 切绿色 + pulseSuccess 动画（nova-ball 过关反馈） */
  success?: boolean
  className?: string
}) {
  const cfg = VARIANT_CFG[variant]
  const useSkew = skew ?? cfg.defaultSkew
  const pct = Math.max(0, Math.min(100, max > 0 ? (value / max) * 100 : 0))
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-md border bg-gradient-to-b from-black/55 to-black/80 shadow-[inset_0_2px_5px_rgba(0,0,0,0.72),inset_0_-1px_0_var(--glass-highlight)] backdrop-blur-glass-md",
        cfg.height,
        cfg.track,
        className,
      )}
      style={{ transform: useSkew ? `skewX(${side === "right" ? 12 : -12}deg)` : undefined }}
    >
      <div
        className={cn(
          "relative h-full rounded-full transition-[width] duration-300 ease-out",
          success
            ? "liquid-success bg-gradient-to-r from-emerald-300 via-green-500 to-lime-400 shadow-glow-cyan"
            : cfg.fill,
        )}
        style={{ width: `${pct}%` }}
      >
        {showHighlight && (
          <span className="pointer-events-none absolute left-[12%] right-[12%] top-px h-px rounded-full bg-white/35 blur-[0.5px]" />
        )}
        {wave && (
          <span
            className="wave-move-anim absolute inset-x-0 top-0 h-1/3 bg-white/25"
            style={{ maskImage: WAVE_MASK, WebkitMaskImage: WAVE_MASK }}
          />
        )}
      </div>
    </div>
  )
}
