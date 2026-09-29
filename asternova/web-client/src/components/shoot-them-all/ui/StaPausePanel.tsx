"use client"

import * as React from "react"
import { motion, useReducedMotion } from "framer-motion"

import { cn } from "@/lib/utils"
import { useDialogA11y } from "@/src/hooks/useDialogA11y"

/**
 * 暂停 · Glassmorphism Panel（art bible §4.4）。
 *
 * 触发：⏸ / Esc。盖全屏 bg-black/45 + backdrop-blur-md（12px）。
 * 面板：宽 420 居中，--glass-bg + --glass-border 1px + 顶部内描边 --glass-highlight
 *       + --elev-lg；.hud-chamfer 斜切 + .hud-scanlines 叠层。
 * **禁霓虹外发光**（不使用 --glow-accent-strong 类外溢光）——这是 §4.4 的硬约束。
 *
 * 条目：标题 PAUSED + 关卡快照 → 继续游戏（主）→ 重新开始（ghost）→
 *       返回大厅（ghost）→ 音量行 → 面板下方比分快照。
 */

type Props = {
  open: boolean
  levelId: number
  levelName: string
  score: number
  targetScore: number
  ballsLeft: number
  onResume: () => void
  onRestart: () => void
  onExit: () => void
  children?: React.ReactNode
}

export function StaPausePanel({
  open,
  levelId,
  levelName,
  score,
  targetScore,
  ballsLeft,
  onResume,
  onRestart,
  onExit,
  children,
}: Props) {
  const reduceMotion = useReducedMotion()
  // 需要显式确认的弹层：Esc = 继续（等同 onResume），故 closeOnEsc 交给外层快捷键，
  // 这里只做焦点陷阱 + 初始聚焦。
  const dialogRef = useDialogA11y<HTMLDivElement>({ open, onClose: onResume, closeOnEsc: false })

  return (
    <motion.div
      className="fixed inset-0 z-[70] flex items-center justify-center p-5"
      initial={false}
      animate={{ opacity: open ? 1 : 0 }}
      transition={reduceMotion ? { duration: 0 } : { duration: 0.2 }}
      style={{ pointerEvents: open ? "auto" : "none" }}
      aria-hidden={!open}
      // 关闭时整棵子树退出 Tab 序（含内嵌 BGM 控件），避免隐形焦点陷阱
      inert={!open}
    >
      {/* 遮罩 */}
      <div className="absolute inset-0 bg-black/45 backdrop-blur-md" />

      <motion.div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="暂停菜单"
        initial={reduceMotion ? false : { opacity: 0, scale: 0.96 }}
        animate={open ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.96 }}
        transition={
          reduceMotion ? { duration: 0 } : { type: "spring", stiffness: 420, damping: 26 }
        }
        className={cn(
          "hud-chamfer relative w-full max-w-[420px] overflow-hidden border border-glass-border bg-glass-bg",
          "shadow-[var(--elev-lg)] backdrop-blur-glass-lg",
        )}
      >
        {/* 顶部内描边高光 */}
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-glass-highlight" />
        {/* 扫描线叠层（同全局透明度语言） */}
        <div className="hud-scanlines pointer-events-none absolute inset-0" />

        <div className="relative z-10 px-7 pb-7 pt-6">
          {/* 标题行 */}
          <div className="flex items-baseline justify-between gap-3">
            <h2 className="font-display text-[22px] leading-none tracking-[0.12em] text-hud-accent">
              PAUSED
            </h2>
            <span className="font-mono-data text-[12px] tracking-[0.14em] text-hud-text-faint">
              第 {String(levelId).padStart(2, "0")} 关 · {levelName}
            </span>
          </div>

          <div className="mt-6 flex flex-col gap-3">
            <button
              type="button"
              onClick={onResume}
              autoFocus
              className={cn(
                "h-[52px] w-full border border-transparent bg-hud-accent text-[15px] font-medium tracking-[0.04em] text-ink-900",
                "transition-[filter,scale] duration-150 ease-[var(--ease-instrument)] hover:brightness-105 active:scale-[0.98]",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hud-accent/60",
              )}
            >
              继续游戏
            </button>

            <button
              type="button"
              onClick={onRestart}
              className={cn(
                "h-[52px] w-full border border-hud-line bg-transparent text-[15px] font-medium tracking-[0.04em] text-hud-text-dim",
                "transition-[color,border-color,scale] duration-150 ease-[var(--ease-instrument)] hover:border-hud-accent/50 hover:text-hud-text active:scale-[0.98]",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hud-accent/60",
              )}
            >
              重新开始
            </button>

            <button
              type="button"
              onClick={onExit}
              className={cn(
                "h-[52px] w-full border border-transparent bg-transparent text-[15px] font-medium tracking-[0.04em] text-hud-text-dim",
                "transition-[color,scale] duration-150 ease-[var(--ease-instrument)] hover:text-hud-text active:scale-[0.98]",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hud-accent/60",
              )}
            >
              返回选关
            </button>
          </div>

          {/* 音量行（§4.4 条目 5）：BGM 滑杆槽。SFX 无音效资产（白皮书 §10 待定），故只留 BGM。 */}
          <div className="mt-5">
            <div className="mb-2 flex items-center gap-2">
              <span className="font-mono-data text-[10px] uppercase tracking-[0.22em] text-hud-text-faint">
                VOLUME
              </span>
              <span className="h-px flex-1 bg-hud-line" />
              <span className="font-mono-data text-[11px] tracking-[0.14em] text-hud-text-faint">
                BGM
              </span>
            </div>
            {children}
          </div>

          {/* 面板下方：比分快照 */}
          <div className="mt-6 flex items-center justify-between border-t border-hud-line pt-4">
            <Snapshot label="SCORE" value={score.toLocaleString("en-US")} />
            <Snapshot label="TARGET" value={targetScore.toLocaleString("en-US")} />
            <Snapshot label="BALLS" value={String(ballsLeft)} />
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}

function Snapshot({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="font-mono-data text-[10px] uppercase tracking-[0.22em] text-hud-text-faint">
        {label}
      </span>
      <span className="font-mono-data text-[13px] tabular-nums text-hud-text-dim">{value}</span>
    </div>
  )
}
