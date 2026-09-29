"use client"

import * as React from "react"
import { animate, useReducedMotion } from "framer-motion"

import { cn } from "@/lib/utils"
import { cinematicEase } from "@/src/lib/motion"

/**
 * 结算数字翻牌（R6 动效轮）：数值从当前显示值补间到目标值。
 *
 * - 时长默认 900ms（--duration-slow「结算/高光」档）+ --ease-cinematic；
 * - 挂载时从 0 起滚（结算语境的情绪点），value 后续变化则从当前值续滚；
 * - reduced-motion 直出终值（framer useReducedMotion + MotionConfig 双保险）；
 * - 无障碍：滚动列 aria-hidden，外层 aria-label 始终朗读最终值（同 RollingNumber 约定）。
 */
export function CountUpValue({
  value,
  duration = 0.9,
  className,
  label,
}: {
  value: number
  /** 补间秒数，默认 0.9（结算/高光档） */
  duration?: number
  className?: string
  /** 无障碍朗读用的纯文本（默认用最终值的千分位形式） */
  label?: string
}) {
  const reduceMotion = useReducedMotion()
  const [shown, setShown] = React.useState(() => (reduceMotion ? value : 0))
  // 镜像当前显示值（只在 effect / 事件回调里写），供 value 变化时续滚
  const shownRef = React.useRef(shown)

  React.useEffect(() => {
    if (reduceMotion) {
      shownRef.current = value
      setShown(value)
      return
    }
    const from = shownRef.current
    if (from === value) return
    const controls = animate(from, value, {
      duration,
      ease: cinematicEase,
      onUpdate: (v) => {
        const next = Math.round(v)
        if (next !== shownRef.current) {
          shownRef.current = next
          setShown(next)
        }
      },
    })
    return () => controls.stop()
  }, [value, duration, reduceMotion])

  const text = (Number.isFinite(shown) ? Math.max(0, shown) : 0).toLocaleString("en-US")
  const finalText = (Number.isFinite(value) ? Math.max(0, Math.floor(value)) : 0).toLocaleString("en-US")

  return (
    <span className={cn("inline-flex items-baseline tabular-nums", className)} aria-label={label ?? finalText}>
      <span aria-hidden="true">{text}</span>
    </span>
  )
}
