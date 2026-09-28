"use client"

import * as React from "react"

import { cn } from "@/lib/utils"

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
 * 当前选中球种持续高亮：外环 --arcade-accent 2px + 底部 2px 琥珀指示条，不悬停也保持 1.12 倍。
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

function falloff(d: number): number {
  const t = Math.max(0, 1 - d / 2)
  return t * t
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
              disabled={off}
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
              onClick={() => {
                if (!off) onSelect(kind)
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
                  borderColor: isCurrent ? "var(--arcade-accent)" : undefined,
                  borderWidth: isCurrent ? 2 : 1,
                  boxShadow: isCurrent ? "inset 0 1px 0 var(--glass-highlight)" : undefined,
                }}
              >
                <BallGlyph kind={kind} size={34} />

                {/* 余量角标（右上，mono-data 12） */}
                <span
                  className="absolute right-0.5 top-0.5 flex h-[17px] min-w-[17px] items-center justify-center bg-hud-sunken px-[3px] font-mono-data text-[11px] leading-none text-hud-text"
                >
                  ×{count}
                </span>

                {/* 选中球种：底部 2px 琥珀指示条 */}
                {isCurrent ? (
                  <span
                    aria-hidden
                    className="absolute bottom-[2px] left-1/2 h-[2px] -translate-x-1/2 bg-hud-accent"
                    style={{ width: SLOT * 0.55 }}
                  />
                ) : null}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
