"use client"

import * as React from "react"
import { motion } from "framer-motion"

import { easeInstrument } from "@/src/lib/motion"

import type { GameEngine, StaHudState } from "./engine/GameEngine"
import { StaBallDock } from "./ui/StaBallDock"
import { StaDynamicIsland } from "./ui/StaDynamicIsland"
import { StaTutorialBar, LEVEL_1_HINTS, type StaHint } from "./ui/StaTutorialBar"

/**
 * 对局 HUD 组合层（art bible §4.1 + §4.3 + §4.6）。
 *
 * 本层只做「信息怎么摆」，全部读数来自 GameEngine.hudSnapshot() 的真实状态，
 * 没有装饰性假数字。真正的屏幕编排（选关 / 暂停 / 结算）在 StaRoot。
 *
 * ⚠️ 尺寸单位是「逻辑画布像素」：本组件位于 StaGameShell 的等比缩放容器内
 * （720×1280），手机竖屏下 scale ≈ 0.5，故字号按 2 倍余量给（§6.2）。
 *
 * 指针分层（§7）：本层除球托槽位与暂停钮外一律 pointer-events-none，
 * 绝不与画布的瞄准/发射抢事件；球托自身也不冒泡到画布。
 */

export function StaHud({
  engine,
  totalBalls,
  clearBanner,
  onPause,
  onBallSelect,
  hints,
  hintAdvanceSignal,
  onHintDismiss,
  seenHintIds,
  interactive,
}: {
  engine: GameEngine | null
  totalBalls: number
  clearBanner: boolean
  onPause: () => void
  onBallSelect: (kind: import("./engine/types").BallKind) => void
  /** 本关教学提示（首关三条，其余关为空） */
  hints: StaHint[]
  hintAdvanceSignal: number | null
  onHintDismiss: () => void
  seenHintIds: string[]
  /** 对局可交互（非暂停 / 非结算）时才允许球托点选 */
  interactive: boolean
}) {
  const [hud, setHud] = React.useState<StaHudState | null>(null)

  React.useEffect(() => {
    if (!engine) {
      setHud(null)
      return
    }
    const tick = () => setHud(engine.hudSnapshot())
    tick()
    // ~10Hz 轮询：跟得上物理手感，又不逐帧 setState 拖累 React
    const id = window.setInterval(tick, 100)
    return () => window.clearInterval(id)
  }, [engine])

  if (!hud) return null

  return (
    <motion.div
      className="pointer-events-none absolute inset-0 z-10 select-none"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.25, ease: easeInstrument }}
    >
      <StaDynamicIsland hud={hud} totalBalls={totalBalls} clearBanner={clearBanner} onPause={onPause} />

      {/* 教学条只在首关出（§4.6「首关三条」）。关号门控在这里收紧：
          否则第 2 关也会弹同一批提示，并把 seen id 写成 2:l1-*（实测踩到）。 */}
      {hints.length > 0 && hud.levelId === 1 ? (
        <StaTutorialBar
          hints={hints}
          levelId={hud.levelId}
          advanceSignal={hintAdvanceSignal}
          onDismiss={onHintDismiss}
          seenIds={seenHintIds}
        />
      ) : null}

      <StaBallDock
        queue={hud.ballQueue}
        current={hud.currentBall}
        onSelect={onBallSelect}
        disabled={!interactive || clearBanner || hud.phase === "level-clear" || hud.phase === "level-fail"}
      />
    </motion.div>
  )
}

export { LEVEL_1_HINTS }
