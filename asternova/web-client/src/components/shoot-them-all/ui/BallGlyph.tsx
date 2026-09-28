"use client"

import * as React from "react"

import type { BallKind } from "../engine/types"

/**
 * 球种微缩图元（SVG，界面层）。
 *
 * 取色严格落 art bible §2.5 的球体表，且全部落在既有 CSS 令牌上，
 * 不新造色板（§2.1 界面层红线）：
 *   standard  → --amber-500 主体 / --amber-400 描边
 *   blast     → --amber-400 主体 / --amber-500 描边 / 核外 --amber-600 暗环
 *   pierce    → --amber-300 主体 / --amber-500 细描边
 *   heavy     → --amber-600（= brass）主体 / --amber-500 粗描边 / --ink-500 赤道环
 *
 * 画布层的球体是 render/ 的程序化绘制（Pixi），本文件只服务 DOM 侧的
 * 球托槽位、HUD 剩余球图标行——两侧同色相不同实现，符合 §2.1 两层分工。
 */

const BALL_STYLE: Record<BallKind, { fill: string; stroke: string; strokeWidth: number }> = {
  standard: { fill: "var(--amber-500)", stroke: "var(--amber-400)", strokeWidth: 1.5 },
  blast: { fill: "var(--amber-400)", stroke: "var(--amber-500)", strokeWidth: 1.5 },
  pierce: { fill: "var(--amber-300)", stroke: "var(--amber-500)", strokeWidth: 1 },
  heavy: { fill: "var(--amber-600)", stroke: "var(--amber-500)", strokeWidth: 2 },
}

export const BALL_KINDS: BallKind[] = ["standard", "blast", "pierce", "heavy"]

export const BALL_KIND_LABEL: Record<BallKind, string> = {
  standard: "标准弹",
  blast: "爆裂弹",
  pierce: "穿透弹",
  heavy: "重弹",
}

export function BallGlyph({
  kind,
  size = 20,
  hollow = false,
  className,
}: {
  kind: BallKind
  /** 外接正方形边长（px，随所在层的单位体系走） */
  size?: number
  /** 已打出的球：空心 + 冷灰描边（art bible §4.1「用掉的变 --ink-500 空心」） */
  hollow?: boolean
  className?: string
}) {
  const s = BALL_STYLE[kind]
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      {hollow ? (
        <circle cx="12" cy="12" r="9" fill="none" stroke="var(--ink-500)" strokeWidth="1.5" />
      ) : (
        <>
          <circle cx="12" cy="12" r="9" fill={s.fill} stroke={s.stroke} strokeWidth={s.strokeWidth} />
          {kind === "blast" ? (
            <circle cx="12" cy="12" r="6" fill="none" stroke="var(--amber-600)" strokeWidth="1.2" opacity="0.5" />
          ) : null}
          {kind === "heavy" ? (
            <path d="M3.6 12h16.8" stroke="var(--ink-500)" strokeWidth="1.2" fill="none" opacity="0.9" />
          ) : null}
          {/* 左上高光点（§2.5：amberPale 圆点偏左上 30%） */}
          <circle cx="9" cy="9" r="2.2" fill="var(--amber-300)" opacity="0.9" />
          {kind === "pierce" ? (
            <circle cx="9" cy="9" r="1.1" fill="#ffffff" opacity="0.7" />
          ) : null}
        </>
      )}
    </svg>
  )
}

/** 星形（选关卡星级 / 教学用）。fill=false 空心。 */
export function StarGlyph({
  filled,
  size = 14,
  color = "var(--hud-accent)",
  hollowColor = "var(--ink-500)",
  className,
}: {
  filled: boolean
  size?: number
  color?: string
  hollowColor?: string
  className?: string
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      <path
        d="M12 2.6l2.72 5.86 6.28.78-4.64 4.36 1.2 6.36L12 16.9l-5.56 3.06 1.2-6.36L3 9.24l6.28-.78z"
        fill={filled ? color : "none"}
        stroke={filled ? color : hollowColor}
        strokeWidth={filled ? 1 : 1.5}
        strokeLinejoin="round"
      />
    </svg>
  )
}

/** 锁图标（选关卡锁定态右上角，art bible §4.2） */
export function LockGlyph({ size = 12, className }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      <rect x="5" y="10.5" width="14" height="10" rx="1.6" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path d="M8.2 10.5V7.8a3.8 3.8 0 0 1 7.6 0v2.7" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}

/** 暂停图标（HUD 右上 ⏸） */
export function PauseGlyph({ size = 22, className }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden="true" focusable="false">
      <rect x="6.5" y="4.5" width="4" height="15" fill="currentColor" />
      <rect x="13.5" y="4.5" width="4" height="15" fill="currentColor" />
    </svg>
  )
}
