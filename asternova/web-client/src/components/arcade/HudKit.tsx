"use client"

import * as React from "react"

import { LiquidBar } from "@/src/components/ui/LiquidBar"
import { cn } from "@/lib/utils"

/**
 * 街机 HUD 原子（Stage A 收编）。
 *
 * 只收编**纯展示、无状态、无定位**的叶子片段：这些游戏里 HUD 有的在外层等比缩放
 * 容器内（star-dash 960x540 画布外壳、merge 400x640），有的全屏自适应
 * （nebula-survivor），所以本文件里**只有排版类**，绝不含 absolute / 定位 / 尺寸外壳 ——
 * 定位与尺寸一律留在各游戏的调用处。
 *
 * 与 ui/LiquidBar.tsx 的分工：进度条本体归 LiquidBar，HudMeter 只是把
 * 「等宽标签 + 进度条 + 等宽读数」这一行的排版收成一处，不改进度条实现。
 */

/** HUD 等宽文字地板：标签与读数共用（字号 / 颜色由调用方按各自配方给） */
const DATA = "font-mono-data"

/** 左标 + 数值（inline）/ 左标 + 右值（split）两种排布 */
export function HudStat({
  label,
  value,
  layout = "inline",
  className,
  labelClassName,
  valueClassName,
}: {
  label?: React.ReactNode
  value?: React.ReactNode
  /** inline：标签与数值同行（原 nebula 击杀 / 得分 / 威胁）· split：两端对齐（原 merge 得分行） */
  layout?: "inline" | "split"
  className?: string
  labelClassName?: string
  valueClassName?: string
}) {
  if (layout === "split") {
    return (
      <div className={cn("flex items-baseline justify-between", className)}>
        <span className={labelClassName}>{label}</span>
        <span className={valueClassName}>{value}</span>
      </div>
    )
  }
  return (
    <span className={cn(className, labelClassName)}>
      {label}
      {" "}
      <span className={valueClassName}>{value}</span>
    </span>
  )
}

/**
 * HUD 顶栏三槽（左 / 中品牌 / 右）。
 *
 * 两个布局都**不额外包一层 dom**，三槽元素原样成为容器的直接子节点 ——
 * 因为调用方依赖 justify-self-* / justify-between 作用在子节点本身，
 * 多包一层 div 会改变栅格项宽度（实测会让 header 的返回按钮被拉伸）。
 */
export function HudTopBar({
  left,
  center,
  right,
  layout = "grid",
  className,
}: {
  left?: React.ReactNode
  center?: React.ReactNode
  right?: React.ReactNode
  /** grid：三等分栅格、品牌严格居中（star-dash）· spread：两端对齐（nebula-survivor） */
  layout?: "grid" | "spread"
  className?: string
}) {
  return (
    <div
      className={cn(
        "relative items-center gap-3",
        layout === "grid" ? "grid grid-cols-[1fr_auto_1fr]" : "flex items-center justify-between",
        className,
      )}
    >
      {left}
      {center}
      {right}
    </div>
  )
}

/**
 * 连击徽标（原 shoot-them-all / StaHud 的 COMBO 章）。
 *
 * 默认类即 StaHud 原样；combo <= 1 时不渲染（与 StaHud 的条件渲染等价）。
 * ⚠️ StaHud 位于 720x1280 逻辑画布内，字号是 2 倍余量值，故本组件不硬编码字号以外的假设。
 */
export function HudComboBadge({
  combo,
  label = "COMBO",
  className,
  countClassName,
  labelClassName,
}: {
  combo: number
  label?: string
  className?: string
  countClassName?: string
  labelClassName?: string
}) {
  if (combo <= 1) return null
  return (
    <div
      className={cn(
        "flex items-baseline gap-2 border border-hud-accent/60 bg-hud-accent/15 px-4 py-1.5 backdrop-blur-sm",
        className,
      )}
    >
      <span
        className={cn(
          "font-display font-bold leading-none tracking-wide text-hud-accent-bright",
          countClassName ?? "text-[34px]",
        )}
      >
        ×{combo}
      </span>
      <span
        className={cn(
          "font-mono-data uppercase tracking-[0.22em] text-hud-accent",
          labelClassName ?? "text-[16px]",
        )}
      >
        {label}
      </span>
    </div>
  )
}

/**
 * 一行仪表：等宽标签 + LiquidBar + 等宽读数。
 * 进度条本体仍由 ui/LiquidBar 负责，这里只做薄封装与整行排版。
 */
export function HudMeter({
  label,
  value,
  max,
  variant,
  text,
  skew,
  wave,
  showHighlight,
  success,
  className,
  labelClassName,
  valueClassName,
  barClassName,
}: {
  label?: React.ReactNode
  value: number
  max: number
  variant: React.ComponentProps<typeof LiquidBar>["variant"]
  /** 右侧读数（如 82/82） */
  text?: React.ReactNode
  skew?: boolean
  wave?: boolean
  showHighlight?: boolean
  success?: boolean
  className?: string
  labelClassName?: string
  valueClassName?: string
  barClassName?: string
}) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      {label != null ? <span className={cn(DATA, labelClassName)}>{label}</span> : null}
      <LiquidBar
        value={value}
        max={max}
        variant={variant}
        skew={skew}
        wave={wave}
        showHighlight={showHighlight}
        success={success}
        className={cn("flex-1 rounded-full", barClassName)}
      />
      {text != null ? <span className={cn(DATA, valueClassName)}>{text}</span> : null}
    </div>
  )
}
