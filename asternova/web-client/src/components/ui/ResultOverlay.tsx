"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { springSnappy } from "@/src/lib/motion"
import { useDialogA11y } from "@/src/hooks/useDialogA11y"
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
  eyebrow,
  highlight,
}: {
  victory: boolean
  title?: string
  subtitle?: string
  stats?: ResultStat[]
  /** 大标题上方的插槽（ArcadeResult 用来放品牌标记） */
  eyebrow?: React.ReactNode
  /** 数值区下方的插槽（ArcadeResult 用来放 NEW RECORD 标记） */
  highlight?: React.ReactNode
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
  const heading = title ?? (victory ? "VICTORY" : "SIGNAL LOST")
  const headingId = React.useId()
  // 标题字号原先写死 clamp(3rem, 9vw, 6.6rem)，是按「4 个字母的短词」估的；
  // 实测 5 个字母的 CRASH 在 1440px 下就被切掉尾字母，VICTORY / DEFEAT 只会更糟。
  // 改为按「最长单词」反推字号，并叠一个 12vw 视口上限兜住窄屏。
  const headingHasCJK = /[\u3400-\u9FFF\uF900-\uFAFF]/.test(heading)
  const longestWord = heading
    .split(/\s+/)
    .reduce((max, w) => Math.max(max, w.length), 1)
  const headingFontSize = headingHasCJK
    ? "min(2.35rem, 7vw)"
    : `min(${(26 / Math.max(longestWord, 4)).toFixed(2)}rem, 12vw)`
  const headingTypeClass = headingHasCJK ? "tracking-[0.06em] not-italic" : "italic tracking-[0.06em]"
  // 结算弹层无「关闭」语义：仅焦点陷阱（Esc 不关闭），与规则弹层的 Esc 行为区分
  const dialogRef = useDialogA11y<HTMLDivElement>({ open: true, onClose: handleSecondary, closeOnEsc: false })

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
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={headingId}
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
              ? "bg-[radial-gradient(1000px_420px_at_50%_40%,rgb(216_163_60/0.16),transparent_60%)]"
              : "bg-[radial-gradient(1000px_420px_at_50%_40%,rgb(192_80_58/0.16),transparent_60%)]",
          )}
        />
        <div className="relative z-10">
          {eyebrow && <div className="mb-4 flex justify-center">{eyebrow}</div>}
          <h2
            id={headingId}
            style={{ fontSize: headingFontSize }}
            className={cn(
              "font-display font-black leading-none",
              headingTypeClass,
              victory
                ? "text-hud-accent drop-shadow-[0_0_50px_rgb(216_163_60/0.55)]"
                : // 失败态原为 Tailwind 原生 red-500 + 高饱和大红辉光，与冷黑/低饱和信号红体系冲突
                  "text-[color:var(--signal-red)] drop-shadow-[0_0_50px_rgb(192_80_58/0.55)]",
            )}
          >
            {heading}
          </h2>

          {/* 2026-09-27 A′：巨型标题保住拉丁展示词的冲击力，中文说明提权到可读主力
              （原为 13px / white·55，实测偏弱，中文承担的信息被压没） */}
          {subtitle && <p className="mt-3 text-[15px] leading-relaxed text-hud-text">{subtitle}</p>}

          {stats && stats.length > 0 && (
            <div className="mt-6 flex items-stretch justify-center gap-6">
              {stats.map((s) => (
                <div key={s.label} className="flex flex-col">
                  <span className="font-mono-data text-2xl font-bold text-white">{s.value}</span>
                  <span className="font-mono-data mt-1 text-[11px] tracking-[0.14em] text-hud-text-dim">
                    {s.label}
                  </span>
                </div>
              ))}
            </div>
          )}

          {highlight && <div className="mt-4 flex justify-center">{highlight}</div>}

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

          {slogan && <p className="mt-6 font-display text-[11px] tracking-[0.32em] text-white/50">{slogan}</p>}
        </div>
      </motion.div>
    </motion.div>
  )
}
