"use client"

import * as React from "react"

import { NODE_CLEAR_RATIO, type GameEngine, type StaHudState } from "./engine/GameEngine"

/**
 * 弹珠风暴 HUD。
 *
 * 在此之前这个游戏**画面上没有任何 HUD** —— 实测只是一片空画布 + 24 颗小六边形，
 * 既不知道得分、也不知道还剩几颗、更不知道打多少算过关（是 5 个游戏里最不像游戏的）。
 * 本 HUD 的全部数值都取自 GameEngine 的真实状态，没有一个是装饰性假数字。
 *
 * ⚠️ 尺寸单位是「逻辑画布像素」：HUD 位于 StaGameShell 的等比缩放容器内（720×1280），
 * 手机竖屏下 scale ≈ 0.5，所以这里必须按 2 倍余量给字号（24–40）才能落到真实 12–20px。
 * 这一点与「交互控件禁止放进 scale 容器」不同：HUD 是 pointer-events-none 的纯展示层。
 */
export function StaHud({ engine }: { engine: GameEngine | null }) {
  const [hud, setHud] = React.useState<StaHudState | null>(null)

  React.useEffect(() => {
    if (!engine) {
      setHud(null)
      return
    }
    const tick = () => setHud(engine.hudSnapshot())
    tick()
    // ~8Hz 轮询：足够跟上物理手感，又不会每帧 setState 拖累 React
    const id = window.setInterval(tick, 120)
    return () => window.clearInterval(id)
  }, [engine])

  if (!hud) return null

  const pct = Math.min(100, Math.round(hud.clearRatio * 100))
  const targetPct = Math.round(NODE_CLEAR_RATIO * 100)
  const cleared = hud.pegsTotal - hud.pegsLeft

  return (
    <div className="pointer-events-none absolute inset-0 z-10 select-none">
      {/* 左上：节点 + 得分 */}
      <div className="absolute left-5 top-5 flex flex-col gap-2">
        <div className="flex items-baseline gap-3 border border-hud-line bg-ink-1000/70 px-4 py-1.5 backdrop-blur-sm">
          <span className="font-mono-data text-[16px] uppercase tracking-[0.24em] text-hud-text-faint">
            NODE
          </span>
          <span className="font-mono-data text-[30px] font-bold leading-none tabular-nums text-hud-paper">
            {String(hud.node).padStart(2, "0")}
          </span>
        </div>
        <div className="flex items-baseline gap-3 border border-hud-line bg-ink-1000/70 px-4 py-1.5 backdrop-blur-sm">
          <span className="font-mono-data text-[16px] uppercase tracking-[0.24em] text-hud-text-faint">
            SCORE
          </span>
          <span className="font-mono-data text-[34px] font-bold leading-none tabular-nums text-hud-accent-bright">
            {hud.score.toLocaleString("en-US")}
          </span>
        </div>
        <div className="flex items-center gap-4 pl-1">
          <span className="font-mono-data text-[17px] tracking-[0.12em] text-hud-text-faint">
            出手 <span className="text-hud-text-dim">{hud.shots}</span>
          </span>
          {hud.bestCombo > 1 ? (
            <span className="font-mono-data text-[17px] tracking-[0.12em] text-hud-text-faint">
              最佳连击 <span className="text-hud-text-dim">{hud.bestCombo}</span>
            </span>
          ) : null}
        </div>
      </div>

      {/* 连击徽标（仅本次出手连击 >1 时出现） */}
      {hud.combo > 1 ? (
        <div className="absolute left-1/2 top-[19%] flex -translate-x-1/2 items-baseline gap-2 border border-hud-accent/60 bg-hud-accent/15 px-4 py-1.5 backdrop-blur-sm">
          <span className="font-display text-[34px] font-bold leading-none tracking-wide text-hud-accent-bright">
            ×{hud.combo}
          </span>
          <span className="font-mono-data text-[16px] uppercase tracking-[0.22em] text-hud-accent">
            COMBO
          </span>
        </div>
      ) : null}

      {/* 底部：清除进度 + 75% 过关刻度 */}
      <div className="absolute inset-x-7 bottom-7">
        <div className="mb-2 flex items-end justify-between">
          <span className="font-mono-data text-[17px] tracking-[0.16em] text-hud-text-faint">
            清除 <span className="text-hud-text-dim">{cleared}</span>
            <span className="text-hud-text-faint">/{hud.pegsTotal}</span>
          </span>
          <span className="font-mono-data text-[17px] tabular-nums text-hud-text-faint">
            过关线 {targetPct}% · {pct}%
          </span>
        </div>
        <div className="relative h-3 overflow-hidden border border-hud-line bg-ink-1000/75">
          <div
            className="h-full bg-hud-accent transition-[width] duration-200 ease-out"
            style={{ width: `${pct}%` }}
          />
          <div className="absolute inset-y-0 w-[2px] bg-hud-paper/80" style={{ left: `${targetPct}%` }} />
        </div>
      </div>
    </div>
  )
}
