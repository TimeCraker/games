"use client"

import * as React from "react"
import { motion, useReducedMotion } from "framer-motion"

import { cn } from "@/lib/utils"

import type { StaHudState } from "../engine/types"
import { BallGlyph, PauseGlyph } from "./BallGlyph"
import { RollingNumber } from "./RollingNumber"

/**
 * HUD · Dynamic Island 胶囊（art bible §4.1）。
 *
 * 顶部居中的胶囊随状态伸缩变形，与星象仪一体（胶囊即仪座，底部留出炮管位，
 * 因此本层绝不画满到炮口，也不画黄铜接口——那是画布层 §3.5/§8 资产 14 的活）。
 *
 * ⚠️ 尺寸单位是「逻辑画布像素」：本组件位于 StaGameShell 的 720×1280 等比缩放容器内，
 * 手机竖屏 scale ≈ 0.5，故字号按 2 倍余量给（§6.2），落到真实屏 12–20px。
 *
 * 胶囊变形按 §5 #10 明确要求「宽高变形 + 内容交叉淡入淡出，220ms --ease-instrument」，
 * 这是 art bible 对「只动 transform/opacity」总则的点名例外（整表 §5 #10），照做。
 */

type Props = {
  hud: StaHudState
  /** 本关球组总数（用于把已打出的球渲染成空心） */
  totalBalls: number
  /** level-clear 的 CLEAR 横幅态 */
  clearBanner: boolean
  onPause: () => void
}

/** §4.1 状态表的胶囊尺寸（逻辑 px） */
function capsuleSize(hud: StaHudState, clearBanner: boolean): { w: number; h: number } {
  if (clearBanner) return { w: 600, h: 80 }
  if (hud.combo > 1) return { w: 560, h: 72 }
  return { w: 420, h: 64 }
}

export function StaDynamicIsland({ hud, totalBalls, clearBanner, onPause }: Props) {
  const reduceMotion = useReducedMotion()
  const { w, h } = capsuleSize(hud, clearBanner)
  const comboActive = hud.combo > 1 && !clearBanner
  const pct = Math.max(0, Math.min(1, hud.progress))

  // 剩余球队列（按打出顺序）+ 已打出的空心位
  const used = Math.max(0, totalBalls - hud.ballQueue.length)
  const dangerLast = hud.ballsLeft === 1 && !clearBanner

  return (
    <div className="pointer-events-none absolute inset-x-0 top-0 z-10 select-none">
      {/* 胶囊：水平居中于 720 逻辑宽，y = 24 */}
      <div
        className="absolute left-1/2 -translate-x-1/2"
        style={{ top: 24, width: w, height: h }}
      >
        <motion.div
          data-active={comboActive ? "true" : undefined}
          className={cn(
            "hud-corners relative flex h-full w-full items-center overflow-hidden",
            "border border-glass-border bg-hud-raised/92 shadow-[inset_0_1px_0_var(--glass-highlight)]",
          )}
          animate={{ width: w, height: h }}
          transition={reduceMotion ? { duration: 0 } : { duration: 0.22, ease: [0.32, 0.72, 0, 1] }}
          style={{ width: w, height: h }}
        >
          {/* 顶部内高光条（玻璃语言，禁外发光） */}
          <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-glass-highlight" />

          {clearBanner ? (
            <ClearBanner stars={hud.stars} />
          ) : (
            <div className="flex w-full items-center justify-center gap-4 px-5">
              {/* 分数 */}
              <div className="flex flex-col items-start">
                <RollingNumber
                  value={hud.score}
                  label={`得分 ${hud.score}`}
                  className="font-mono-data text-[40px] font-bold leading-none text-hud-text"
                />
              </div>

              {/* 分隔竖线 */}
              <div className="h-7 w-px bg-hud-line-strong" />

              {/* 目标 + 进度槽 */}
              <div className="flex flex-col items-start gap-1.5">
                <div className="flex items-baseline gap-1.5">
                  <span className="font-mono-data text-[20px] tracking-[0.14em] text-hud-text-faint">目标</span>
                  <span className="font-mono-data text-[22px] font-semibold leading-none tabular-nums text-hud-text-dim">
                    {hud.targetScore.toLocaleString("en-US")}
                  </span>
                </div>
                {/* 细进度槽：宽 72 高 4（§4.1） */}
                <div className="h-1 w-[72px] overflow-hidden bg-hud-sunken">
                  <div
                    className="h-full bg-hud-accent transition-[width] duration-200 ease-out"
                    style={{ width: `${Math.round(pct * 100)}%` }}
                  />
                </div>
              </div>

              {/* 分隔竖线 */}
              <div className="h-7 w-px bg-hud-line-strong" />

              {/* 剩余球图标行 */}
              <div className="flex items-center gap-[5px]">
                {Array.from({ length: used }, (_, i) => (
                  <BallGlyph key={`used-${i}`} kind="standard" size={10} hollow />
                ))}
                {hud.ballQueue.map((k, i) => (
                  <span
                    key={`left-${i}`}
                    className={cn(
                      "inline-flex",
                      // 险胜：最后 1 枚加 --hud-red 呼吸描边（§4.1）
                      dangerLast && i === 0 && "rounded-full ring-1 ring-hud-red motion-safe:animate-pulse",
                    )}
                  >
                    <BallGlyph kind={k} size={10} />
                  </span>
                ))}
                {used === 0 && hud.ballQueue.length === 0 ? (
                  <span className="font-mono-data text-[18px] text-hud-text-faint">—</span>
                ) : null}
              </div>

              {/* 连击区（条件展开，§4.1「连击中」） */}
              <motion.div
                className="flex items-baseline gap-1.5 overflow-hidden"
                initial={false}
                animate={{
                  width: comboActive ? 96 : 0,
                  opacity: comboActive ? 1 : 0,
                }}
                transition={reduceMotion ? { duration: 0 } : { duration: 0.22, ease: [0.32, 0.72, 0, 1] }}
              >
                <motion.span
                  key={hud.combo}
                  className="font-mono-data text-[28px] font-bold leading-none text-hud-accent-bright"
                  initial={reduceMotion ? false : { scale: 1 }}
                  animate={reduceMotion ? undefined : { scale: [1, 1.25, 1] }}
                  transition={{ duration: 0.15, ease: [0.32, 0.72, 0, 1] }}
                >
                  ×{hud.combo}
                </motion.span>
                <span className="font-mono-data text-[18px] uppercase tracking-[0.22em] text-hud-accent">
                  COMBO
                </span>
              </motion.div>
            </div>
          )}
        </motion.div>
      </div>

      {/* 暂停钮 ⏸：视觉 56×56，热区 88 逻辑（§4.1/§7）。
          独立于胶囊（x 636–692），指针事件只此钮开口，不抢画布瞄准。 */}
      <button
        type="button"
        onClick={onPause}
        aria-label="暂停"
        title="暂停"
        className="pointer-events-auto absolute flex items-center justify-center border-0 bg-transparent p-0 text-hud-text outline-none focus-visible:ring-2 focus-visible:ring-hud-accent"
        style={{ left: 636 - 16, top: 24 - 16, width: 88, height: 88 }}
      >
        <span className="hud-chamfer-sm flex h-[56px] w-[56px] items-center justify-center border border-glass-border bg-glass-bg text-hud-text transition-colors duration-150 hover:text-hud-accent active:scale-[0.98]">
          <PauseGlyph size={22} />
        </span>
      </button>
    </div>
  )
}

/** 过关瞬间的 CLEAR 横幅（§4.1 状态表末行：600×80，--hud-green） */
function ClearBanner({ stars }: { stars: number }) {
  return (
    <div className="flex w-full flex-col items-center justify-center gap-1">
      <span className="font-display text-[42px] leading-none tracking-[0.06em] text-hud-green">CLEAR</span>
      <span className="font-mono-data text-[18px] tracking-[0.28em] text-hud-text-dim">
        {"★".repeat(Math.max(0, Math.min(3, stars)))}
        {"☆".repeat(3 - Math.max(0, Math.min(3, stars)))}
      </span>
    </div>
  )
}
