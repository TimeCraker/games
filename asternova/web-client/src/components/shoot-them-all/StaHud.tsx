"use client"

import * as React from "react"

import type { GameEngine, StaHudState } from "./engine/GameEngine"

/**
 * 弹珠风暴 HUD（关卡制白皮书 §5 版，最小适配）。
 *
 * 全部数值取自 GameEngine.hudSnapshot() 的真实状态，没有装饰性假数字。
 * 视觉精雕是下一波美术/UI agent 的事，这里只保证信息完整可读。
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

  const pct = Math.min(100, Math.round(hud.progress * 100))
  const ballLabel: Record<string, string> = {
    standard: "标",
    blast: "爆",
    pierce: "穿",
    heavy: "重",
  }

  return (
    <div className="pointer-events-none absolute inset-0 z-10 select-none">
      {/* 左上：关卡 + 得分/目标 */}
      <div className="absolute left-5 top-5 flex flex-col gap-2">
        <div className="flex items-baseline gap-3 border border-hud-line bg-ink-1000/70 px-4 py-1.5 backdrop-blur-sm">
          <span className="font-mono-data text-[16px] uppercase tracking-[0.24em] text-hud-text-faint">
            LV
          </span>
          <span className="font-mono-data text-[30px] font-bold leading-none tabular-nums text-hud-paper">
            {String(hud.levelId).padStart(2, "0")}
          </span>
          <span className="font-mono-data text-[18px] tracking-[0.12em] text-hud-text-dim">
            {hud.levelName}
          </span>
        </div>
        <div className="flex items-baseline gap-3 border border-hud-line bg-ink-1000/70 px-4 py-1.5 backdrop-blur-sm">
          <span className="font-mono-data text-[16px] uppercase tracking-[0.24em] text-hud-text-faint">
            SCORE
          </span>
          <span className="font-mono-data text-[34px] font-bold leading-none tabular-nums text-hud-accent-bright">
            {hud.score.toLocaleString("en-US")}
          </span>
          <span className="font-mono-data text-[18px] tabular-nums text-hud-text-faint">
            / {hud.targetScore.toLocaleString("en-US")}
          </span>
        </div>
        <div className="flex items-center gap-4 pl-1">
          <span className="font-mono-data text-[17px] tracking-[0.12em] text-hud-text-faint">
            球 <span className="text-hud-text-dim">{hud.ballsLeft}</span>
          </span>
          {hud.bestCombo > 1 ? (
            <span className="font-mono-data text-[17px] tracking-[0.12em] text-hud-text-faint">
              最佳连击 <span className="text-hud-text-dim">{hud.bestCombo}</span>
            </span>
          ) : null}
        </div>
      </div>

      {/* 右上：球组队列（按打出顺序，当前球高亮） */}
      <div className="absolute right-5 top-5 flex flex-col items-end gap-2">
        <span className="font-mono-data text-[15px] uppercase tracking-[0.22em] text-hud-text-faint">
          BALLS
        </span>
        <div className="flex gap-1.5">
          {hud.ballQueue.map((k, i) => (
            <span
              key={`${k}-${i}`}
              className={
                i === 0
                  ? "flex h-11 w-11 items-center justify-center border border-hud-accent bg-hud-accent/25 font-display text-[19px] font-bold text-hud-accent-bright"
                  : "flex h-11 w-11 items-center justify-center border border-hud-line bg-ink-1000/70 font-display text-[19px] text-hud-text-dim"
              }
            >
              {ballLabel[k] ?? "?"}
            </span>
          ))}
          {hud.ballQueue.length === 0 ? (
            <span className="flex h-11 items-center px-2 font-mono-data text-[16px] text-hud-text-faint">
              —
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

      {/* 终态角标：过关星级 / 未达标 */}
      {hud.phase === "level-clear" ? (
        <div className="absolute left-1/2 top-[30%] flex -translate-x-1/2 flex-col items-center gap-2 border border-hud-accent/60 bg-hud-accent/15 px-8 py-4 backdrop-blur-sm">
          <span className="font-display text-[40px] leading-none tracking-wide text-hud-accent-bright">
            {"★".repeat(hud.stars)}
            {"☆".repeat(3 - hud.stars)}
          </span>
          <span className="font-mono-data text-[18px] uppercase tracking-[0.28em] text-hud-paper">
            LEVEL CLEAR
          </span>
        </div>
      ) : null}
      {hud.phase === "level-fail" ? (
        <div className="absolute left-1/2 top-[30%] flex -translate-x-1/2 flex-col items-center gap-2 border border-hud-line bg-ink-1000/80 px-8 py-4 backdrop-blur-sm">
          <span className="font-display text-[32px] leading-none tracking-wide text-hud-text-dim">
            未达标
          </span>
          <span className="font-mono-data text-[18px] uppercase tracking-[0.28em] text-hud-text-faint">
            {hud.score.toLocaleString("en-US")} / {hud.targetScore.toLocaleString("en-US")}
          </span>
        </div>
      ) : null}

      {/* 底部：得分进度条 */}
      <div className="absolute inset-x-7 bottom-7">
        <div className="mb-2 flex items-end justify-between">
          <span className="font-mono-data text-[17px] tracking-[0.16em] text-hud-text-faint">
            钉 <span className="text-hud-text-dim">{hud.pegsTotal - hud.pegsLeft}</span>
            <span className="text-hud-text-faint">/{hud.pegsTotal}</span>
          </span>
          <span className="font-mono-data text-[17px] tabular-nums text-hud-text-faint">
            目标进度 {pct}%
          </span>
        </div>
        <div className="relative h-3 overflow-hidden border border-hud-line bg-ink-1000/75">
          <div
            className="h-full bg-hud-accent transition-[width] duration-200 ease-out"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </div>
  )
}
