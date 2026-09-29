"use client"

import * as React from "react"
import { motion } from "framer-motion"

import { cn } from "@/lib/utils"
import { springSnappy } from "@/src/lib/motion"

import type { BallKind } from "../engine/types"
import { BALL_KINDS, BALL_KIND_LABEL, BallGlyph } from "./BallGlyph"

/**
 * 球托 · Dock Magnification（art bible §4.3）。
 *
 * 底部横排球列（y 1148–1252，逻辑 px），macOS Dock 式距离衰减放大：
 *   scale(i) = 1 + 0.35 × falloff(d)，falloff = max(0, 1 − d/2)²，d = 与悬停槽的距离（槽为单位）
 *   → 悬停槽 1.35、邻槽 1.09、再邻 1.0（§9 验收点）。
 *
 * 槽位 = 球种（4 个固定槽），不是逐颗球。理由是 §4.3 自身的两条规格只在「球种槽」下成立：
 * 「余量角标：每槽右上角 mono-data 12 的数字徽章」+「×0 时整槽降为 35% 亮度 + 禁点」——
 * 逐颗球的槽位没有「余量」可言，也不会出现 ×0。§4.1 的球托图 `● ● ◉ ●` 也是 4 槽。
 * 余量仍取自 hudSnapshot().ballQueue（按球种聚合计数），点选调 selectBall(kind)。
 *
 * 只动 transform（scale + translateY），180ms `--ease-instrument`（§5 #8）。
 * R6：选中态改 morphing 滑块 —— 琥珀环 + 底部指示条整体（x 弹簧滑动），弃原地变色（§5.3）。
 * 空槽（×0）点击给 WAAPI shake 反馈（composite:"add" 叠加在 hover scale 上）。
 * 球种图标复用 BallGlyph（3.1 球体微缩版的界面层实现），不另画图标。
 *
 * 触控：视觉槽 72×72 + 间距 12；命中区扩到 88 逻辑（真实 ≥44px，§7）；
 * 按住 = 持续放大预览（同悬停但更稳）。
 *
 * 指针分层（§7 防误触）：本层 pointer-events-auto 吃掉 Dock 区的手势，
 * 使「Dock 区拖动只切球不发射」；画布层的手势靠 pointer capture 保持连贯，
 * 两者不共享事件路径。
 */

const SLOT = 72
const GAP = 12
const HIT = 88
/** 槽位外框节奏：负外边距把 88 命中区折进 72+12 的视觉网格，SLOT 盒起点 = i*(SLOT+GAP) */
const STEP = SLOT + GAP
/** 滑块比 SLOT 盒外扩 4px 成环 */
const PILL_INSET = 4

function falloff(d: number): number {
  const t = Math.max(0, 1 - d / 2)
  return t * t
}

/** 空槽 shake：WAAPI composite:"add" 叠加在槽体现有 scale transform 上 */
function shakeSlot(el: HTMLElement | null): void {
  if (!el || typeof el.animate !== "function") return
  el.animate(
    [
      { transform: "translateX(0)" },
      { transform: "translateX(-3px)" },
      { transform: "translateX(3px)" },
      { transform: "translateX(-3px)" },
      { transform: "translateX(3px)" },
      { transform: "translateX(0)" },
    ],
    { duration: 160, easing: "cubic-bezier(0.32, 0.72, 0, 1)", composite: "add" },
  )
}

export function StaBallDock({
  queue,
  current,
  onSelect,
  disabled = false,
}: {
  /** 剩余球种队列（按打出顺序），来自 hudSnapshot().ballQueue */
  queue: BallKind[]
  /** 当前选中球种 */
  current: BallKind | null
  onSelect: (kind: BallKind) => void
  /** level-clear / level-fail 等终态时禁点 */
  disabled?: boolean
}) {
  const [hoverIdx, setHoverIdx] = React.useState<number | null>(null)
  const [pressedIdx, setPressedIdx] = React.useState<number | null>(null)

  // 余量：按球种聚合计数（角标用）
  const counts = React.useMemo(() => {
    const m = new Map<BallKind, number>()
    for (const k of queue) m.set(k, (m.get(k) ?? 0) + 1)
    return m
  }, [queue])

  // 当前选中球种：优先飞在场上的，其次队首
  const activeKind: BallKind | null = current ?? queue[0] ?? null
  const activeIdx = activeKind ? BALL_KINDS.indexOf(activeKind) : -1
  const active = pressedIdx ?? hoverIdx

  return (
    <div
      className="pointer-events-auto absolute inset-x-0 z-10 flex justify-center"
      style={{ top: 1148, height: 1252 - 1148 }}
      onPointerLeave={() => {
        setHoverIdx(null)
        setPressedIdx(null)
      }}
    >
      <div className="relative flex items-center" style={{ gap: GAP }}>
        {/* R6 morphing 选中滑块：琥珀环 + 底部指示条一体，x 弹簧滑到当前槽 */}
        <motion.span
          aria-hidden
          className="pointer-events-none absolute z-10 border-2"
          style={{
            width: SLOT + PILL_INSET * 2,
            height: SLOT + PILL_INSET * 2,
            top: "50%",
            left: 0,
            marginTop: -(SLOT + PILL_INSET * 2) / 2,
            borderColor: "var(--arcade-accent)",
          }}
          initial={false}
          animate={{
            x: activeIdx * STEP - PILL_INSET,
            opacity: activeIdx >= 0 ? 1 : 0,
          }}
          transition={activeIdx >= 0 ? springSnappy : { duration: 0.15 }}
        >
          <span
            className="absolute bottom-[2px] left-1/2 h-[2px] -translate-x-1/2 bg-hud-accent"
            style={{ width: SLOT * 0.55 }}
          />
        </motion.span>

        {BALL_KINDS.map((kind, i) => {
          const d = active === null ? Infinity : Math.abs(i - active)
          const mag = active === null ? 0 : 0.35 * falloff(d)
          const isCurrent = kind === activeKind
          // 选中球即使不悬停也保持 1.12；悬停/按住时按距离衰减放大（1.35 > 1.12 取大）
          const scale = Math.max(isCurrent ? 1.12 : 1, 1 + mag)
          const lift = active !== null && d === 0 ? -6 : 0
          const count = counts.get(kind) ?? 0
          const empty = count === 0
          const off = disabled || empty

          return (
            <button
              key={kind}
              type="button"
              // 空槽保持可点击以给 shake 反馈（R6）；终态禁用仍然真 disabled
              disabled={disabled}
              aria-disabled={empty || undefined}
              aria-label={`${BALL_KIND_LABEL[kind]}，余量 ${count}`}
              aria-pressed={isCurrent}
              title={BALL_KIND_LABEL[kind]}
              className={cn(
                "relative border-0 bg-transparent p-0 outline-none",
                "focus-visible:ring-2 focus-visible:ring-hud-accent",
                off && "cursor-not-allowed",
              )}
              style={{
                // 命中区 88×88 逻辑（真实 ≥44px，§7）。此前误用 SLOT(72) 当宽度，
                // 375px 视口实测仅 37.5 真实 px。负外边距抵消 88 与 72 的差，
                // 保住槽位 72 + 间距 12 的视觉节奏不被撑开。
                width: HIT,
                height: HIT,
                marginInline: -(HIT - SLOT) / 2,
                opacity: empty ? 0.35 : 1,
              }}
              onPointerEnter={() => setHoverIdx(i)}
              onPointerDown={() => setPressedIdx(i)}
              onPointerUp={() => setPressedIdx(null)}
              onPointerCancel={() => setPressedIdx(null)}
              onPointerLeave={() => {
                setHoverIdx((v) => (v === i ? null : v))
                setPressedIdx(null)
              }}
              onClick={(e) => {
                if (disabled) return
                if (empty) {
                  // shake 挂在 button 本体（无 base transform，免 composite），槽体 hover scale 不受扰
                  shakeSlot(e.currentTarget)
                  return
                }
                onSelect(kind)
              }}
            >
              {/* 视觉槽体 */}
              <span
                className="absolute left-1/2 top-1/2 flex items-center justify-center border border-hud-line bg-ink-800/80"
                style={{
                  width: SLOT,
                  height: SLOT,
                  transform: `translate(-50%, -50%) scale(${scale}) translateY(${lift}px)`,
                  transition: "transform 180ms var(--ease-instrument)",
                }}
              >
                <BallGlyph kind={kind} size={34} />

                {/* 余量角标（右上，mono-data 12） */}
                <span
                  className="absolute right-0.5 top-0.5 flex h-[17px] min-w-[17px] items-center justify-center bg-hud-sunken px-[3px] font-mono-data text-[11px] leading-none text-hud-text"
                >
                  ×{count}
                </span>
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
