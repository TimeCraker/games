"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { springSnappy } from "@/src/lib/motion"
import { cn } from "@/lib/utils"

/**
 * 统一结算浮层（Stage A 共享组件）
 * 容器用 nebula-survivor:713-721 玻璃 + springSnappy；cinematic 态叠 arena:362-381 扫描线
 * 替换 5 处结算实现：arena inline cyber、nebula、nova-ball CSS panel、merge、star-dash canvas fillText
 *
 * 调用方需用 <AnimatePresence> 包裹以启用 exit 动画。
 */
export type ResultStat = { label: string; value: string | number }

export function ResultOverlay({
  victory,
  title,
  subtitle,
  stats,
  actionLabel = "重新开始",
  onAction,
  secondaryLabel = "返回大厅",
  onSecondary,
  slogan = "Reach Beyond the Stars",
  cinematic = false,
  className,
}: {
  victory: boolean
  title?: string
  subtitle?: string
  stats?: ResultStat[]
  actionLabel?: string
  onAction?: () => void
  secondaryLabel?: string
  /** 默认 router.push("/lobby") */
  onSecondary?: () => void
  slogan?: string
  /** 叠 arena 风格 CRT 扫描线 */
  cinematic?: boolean
  className?: string
}) {
  const router = useRouter()
  const handleSecondary = onSecondary ?? (() => router.push("/lobby"))
  const heading = title ?? (victory ? "VICTORY" : "信号丢失")

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 z-[60] flex items-center justify-center bg-black/65 p-5 backdrop-blur-md"
    >
      {cinematic && (
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.16]"
          style={{
            background:
              "repeating-linear-gradient(0deg, transparent 0, transparent 2px, rgba(255,255,255,0.5) 3px, transparent 4px)",
          }}
        />
      )}
      <motion.div
        initial={{ opacity: 0, scale: 0.94, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96 }}
        transition={springSnappy}
        className={cn(
          "relative w-full max-w-md overflow-hidden rounded-[1.75rem] border border-glass-border bg-glass-bg p-7 text-center shadow-lg backdrop-blur-glass-lg",
          className,
        )}
      >
        <div
          className={cn(
            "pointer-events-none absolute inset-0",
            victory
              ? "bg-[radial-gradient(1000px_420px_at_50%_40%,oklch(0.78_0.16_220/0.18),transparent_60%)]"
              : "bg-[radial-gradient(1000px_420px_at_50%_40%,oklch(0.6_0.22_25/0.16),transparent_60%)]",
          )}
        />
        <div className="relative z-10">
          <h2
            className={cn(
              "font-display text-[clamp(3rem,9vw,6.6rem)] font-black italic leading-none tracking-widest",
              victory
                ? "text-cyan-400 drop-shadow-[0_0_50px_rgba(34,211,238,0.8)]"
                : "text-red-500 drop-shadow-[0_0_50px_rgba(220,38,38,0.8)]",
            )}
          >
            {heading}
          </h2>

          {subtitle && <p className="mt-3 text-sm text-white/55">{subtitle}</p>}

          {stats && stats.length > 0 && (
            <div className="mt-6 flex items-stretch justify-center gap-6">
              {stats.map((s) => (
                <div key={s.label} className="flex flex-col">
                  <span className="font-mono-data text-2xl font-bold text-white">{s.value}</span>
                  <span className="font-mono-data mt-1 text-[10px] uppercase tracking-[0.18em] text-white/40">
                    {s.label}
                  </span>
                </div>
              ))}
            </div>
          )}

          <div className="mt-8 flex flex-col gap-2.5">
            {onAction && (
              <Button variant="default" size="lg" onClick={onAction} className="w-full">
                {actionLabel}
              </Button>
            )}
            <Button
              variant="ghost"
              size="lg"
              onClick={handleSecondary}
              className="w-full text-white/70 hover:text-white"
            >
              {secondaryLabel}
            </Button>
          </div>

          {slogan && <p className="mt-6 font-display text-[11px] tracking-[0.32em] text-white/30">{slogan}</p>}
        </div>
      </motion.div>
    </motion.div>
  )
}
