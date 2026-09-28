"use client"

import * as React from "react"
import { motion, useReducedMotion } from "framer-motion"

import { cn } from "@/lib/utils"

import { markHintSeen } from "./staProgress"

/**
 * 教学 / 首次提示条（art bible §4.6）。
 *
 * 形态：轻量提示条，不是弹窗 —— 贴在球托上方（y 1080–1140，逻辑 px），
 * 宽 560 居中，高 52。.hud-chamfer-sm + --hud-raised 底 + --glass-border；
 * 左端步骤序号 1/3（mono-data 12，--hud-accent）；正文 14px --hud-text；
 * 右端「知道了」ghost 链接。
 *
 * 行为：进场 slide-up 12px + fade 220ms；玩家完成对应动作或 6s 后自动淡出；
 * 同一提示同关只出一次（hintId 带关号，落到 staProgress.hintsSeen）。
 *
 * 显示第几条**直接由 seenIds 派生**，不另存 idx state —— 早先 state+effect 双写
 * 与外部推进信号会打架（重复 markHintSeen / 跳条）。seenIds 是唯一真源。
 *
 * 禁：全屏遮罩引导、手指动画盖住瞄准线、连环弹窗。
 */

export type StaHint = {
  /** 唯一 id（写入进度存储用） */
  id: string
  /** 正文 */
  text: string
}

/** 首关三条（§4.6 内容） */
export const LEVEL_1_HINTS: StaHint[] = [
  { id: "l1-aim", text: "拖动瞄准，松手发射" },
  { id: "l1-peg", text: "点亮所有晶体钉得分" },
  { id: "l1-star", text: "剩余球越多，星级越高" },
]

export function StaTutorialBar({
  hints,
  levelId,
  autoHideMs = 6000,
  /** 玩家完成对应动作时由外部推进（如发出第一球）；null = 尚未有动作 */
  advanceSignal,
  onDismiss,
  seenIds,
}: {
  hints: StaHint[]
  levelId: number
  autoHideMs?: number
  advanceSignal?: number | null
  onDismiss?: () => void
  seenIds: string[]
}) {
  const reduceMotion = useReducedMotion()

  const scopedId = React.useCallback((hintId: string) => `${levelId}:${hintId}`, [levelId])

  // 首条「未看过」的提示；全看完 → -1（不渲染）
  const idx = React.useMemo(() => {
    for (let i = 0; i < hints.length; i++) {
      if (!seenIds.includes(scopedId(hints[i].id))) return i
    }
    return -1
  }, [hints, seenIds, scopedId])

  const current = idx >= 0 ? hints[idx] : null

  const advance = React.useCallback(() => {
    if (!current) return
    markHintSeen(scopedId(current.id))
    // 全部看完才收摊（否则交给派生的 idx 自然跳到下一条）
    const allDone = idx + 1 >= hints.length
    if (allDone) onDismiss?.()
  }, [current, idx, hints.length, scopedId, onDismiss])

  // 6s 自动淡出到下一条 / 收摊
  React.useEffect(() => {
    if (!current) return
    const t = window.setTimeout(advance, autoHideMs)
    return () => window.clearTimeout(t)
  }, [current, autoHideMs, advance])

  // 外部动作信号推进：只在信号真正变化时推一次
  const lastSignal = React.useRef<number | null>(null)
  React.useEffect(() => {
    if (advanceSignal == null) return
    if (lastSignal.current === advanceSignal) return
    lastSignal.current = advanceSignal
    advance()
  }, [advanceSignal, advance])

  if (!current) return null

  return (
    <motion.div
      className="pointer-events-auto absolute inset-x-0 z-10 flex justify-center"
      style={{ top: 1080, height: 60 }}
      initial={reduceMotion ? false : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={reduceMotion ? undefined : { opacity: 0 }}
      transition={reduceMotion ? { duration: 0 } : { duration: 0.22, ease: [0.32, 0.72, 0, 1] }}
    >
      <div
        data-sta-hint="true"
        className={cn(
          "hud-chamfer-sm flex h-[52px] w-[560px] items-center gap-3 px-4",
          "border border-glass-border bg-hud-raised",
        )}
      >
        <span className="font-mono-data text-[12px] tracking-[0.22em] text-hud-accent">
          {idx + 1}/{hints.length}
        </span>
        <p className="flex-1 text-[14px] leading-snug text-hud-text">{current.text}</p>
        <button
          type="button"
          onClick={advance}
          className={cn(
            "shrink-0 border-0 bg-transparent px-2 py-1 text-[13px] text-hud-text-dim",
            "transition-colors duration-150 hover:text-hud-text active:scale-[0.98]",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hud-accent/60",
          )}
        >
          知道了
        </button>
      </div>
    </motion.div>
  )
}
