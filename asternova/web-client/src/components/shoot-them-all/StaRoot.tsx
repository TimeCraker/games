"use client"

import * as React from "react"

import { GameBackButton } from "@/src/components/ui/GameBackButton"

import { StaGameShell } from "./StaGameShell"
import { StaPixiApp } from "./render/StaPixiApp"

/**
 * Shoot Them All v2 顶层根（Stage Spec §8.11 StaRoot）。
 * PixiCanvasHost + overlay + 与引擎桥接（M1 阶段仅 Pixi 主机 + 星空背景）。
 */
export function StaRoot() {
  const hostRef = React.useRef<HTMLDivElement | null>(null)
  const pixiRef = React.useRef<StaPixiApp | null>(null)
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
        // StrictMode 双调用兜底：挂载完成后若已被取消，立即销毁避免孤儿 app
        if (cancelled) {
          pixi.destroy()
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      })

    return () => {
      cancelled = true
      pixi.destroy()
      pixiRef.current = null
    }
  }, [])

  return (
    <StaGameShell>
      <div ref={hostRef} className="absolute inset-0 z-0" />

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
