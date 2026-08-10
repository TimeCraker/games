"use client"

import * as React from "react"

import { GameBackButton } from "@/src/components/ui/GameBackButton"
import { HEIGHT, WIDTH } from "./constants"
import { StaGameShell } from "./StaGameShell"
import { StaPixiApp } from "./render/StaPixiApp"

/**
 * Shoot Them All v2 顶层根（Stage Spec §8.11 StaRoot）。
 * 拥有 Pixi 主机生命周期 + 指针输入 → 引擎桥接 + UI overlay。
 *
 * 输入模型（Stage Spec §3.3）：
 * - 鼠标：悬停瞄准（实时），单击发射。
 * - 触屏：按下拖动瞄准，松开发射。
 * 统一为 pointer 事件：move/down 更新瞄准，up 发射。
 */
export function StaRoot() {
  const hostRef = React.useRef<HTMLDivElement | null>(null)
  const pixiRef = React.useRef<StaPixiApp | null>(null)
  const engineRef = React.useRef<ReturnType<StaPixiApp["gameEngine"]> | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    const host = hostRef.current
    if (!host) return

    const pixi = new StaPixiApp()
    pixiRef.current = pixi
    let cancelled = false

    pixi
      .mount(host)
      .then(() => {
        if (cancelled) {
          pixi.destroy()
          return
        }
        engineRef.current = pixi.gameEngine
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      })

    return () => {
      cancelled = true
      pixi.destroy()
      pixiRef.current = null
      engineRef.current = null
    }
  }, [])

  /** 客户端坐标 → 逻辑画布坐标（720×1280），补偿 StaGameShell 的等比缩放。 */
  const toLogical = React.useCallback((clientX: number, clientY: number) => {
    const host = hostRef.current
    if (!host) return null
    const rect = host.getBoundingClientRect()
    if (rect.width === 0 || rect.height === 0) return null
    return {
      x: ((clientX - rect.left) / rect.width) * WIDTH,
      y: ((clientY - rect.top) / rect.height) * HEIGHT,
    }
  }, [])

  const onPointerMove = React.useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      const p = toLogical(e.clientX, e.clientY)
      if (p) engineRef.current?.setAimFromPoint(p.x, p.y)
    },
    [toLogical],
  )

  const onPointerDown = React.useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      const p = toLogical(e.clientX, e.clientY)
      if (p) engineRef.current?.setAimFromPoint(p.x, p.y)
    },
    [toLogical],
  )

  const onPointerUp = React.useCallback(() => {
    engineRef.current?.launch()
  }, [])

  return (
    <StaGameShell>
      <div
        ref={hostRef}
        className="absolute inset-0 z-0"
        style={{ touchAction: "none" }}
        onPointerMove={onPointerMove}
        onPointerDown={onPointerDown}
        onPointerUp={onPointerUp}
      />

      <div className="pointer-events-none absolute inset-x-0 top-0 z-20 flex items-center justify-between p-3">
        <span className="font-mono-data text-[10px] uppercase tracking-[0.22em] text-white/40">
          Shoot Them All · v2
        </span>
        <div className="pointer-events-auto">
          <GameBackButton />
        </div>
      </div>

      {error ? (
        <div className="absolute inset-0 z-30 flex items-center justify-center bg-black/70 p-6 text-center text-sm text-white/80">
          引擎初始化失败：{error}
        </div>
      ) : null}
    </StaGameShell>
  )
}
