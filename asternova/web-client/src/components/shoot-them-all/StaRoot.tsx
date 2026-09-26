"use client"

import * as React from "react"

import { BrandMark } from "@/src/components/arcade/BrandMark"
import { useArcadeAccent } from "@/src/components/arcade/useArcadeAccent"
import { GameBackButton } from "@/src/components/ui/GameBackButton"
import type { GameEngine } from "./engine/GameEngine"
import { HEIGHT, WIDTH } from "./constants"
import { StaGameShell } from "./StaGameShell"
import { StaHud } from "./StaHud"
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
  useArcadeAccent("shoot-them-all")
  const hostRef = React.useRef<HTMLDivElement | null>(null)
  const pixiRef = React.useRef<StaPixiApp | null>(null)
  // 注：StaPixiApp.gameEngine 是 getter，其类型已是返回值本身，
  // 套 ReturnType<> 会让 tsc 报「不是函数类型」，故直接标注类类型。
  const engineRef = React.useRef<GameEngine | null>(null)
  // HUD 需要引擎实例才能轮询读数。不能直接在渲染期读 engineRef（React 规则：
  // "Cannot access refs during render"），故挂载完成后再落到 state。
  const [engine, setEngine] = React.useState<GameEngine | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    const host = hostRef.current
    if (!host) return

    // Pixi v8 会在初始化期间（时机不定）注入 1×1 的无语义 accessibility 按钮节点；
    // 一次性销毁可能发生在节点创建之前而漏网。用 MutationObserver 兜底移除，
    // 避免键盘 Tab 落入隐形的 1px 焦点陷阱。
    const cleanPixiA11yNodes = () => {
      host.querySelectorAll<HTMLElement>('button[title*="enable accessibility"], [aria-label*="enable accessibility"]').forEach((n) => n.remove())
    }
    cleanPixiA11yNodes()
    const mo = new MutationObserver(cleanPixiA11yNodes)
    mo.observe(host, { childList: true, subtree: true })

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
        setEngine(pixi.gameEngine)
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      })

    return () => {
      mo.disconnect()
      cancelled = true
      pixi.destroy()
      pixiRef.current = null
      engineRef.current = null
      setEngine(null)
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
    <>
      <StaGameShell>
        <div
          ref={hostRef}
          className="absolute inset-0 z-0"
          style={{ touchAction: "none" }}
          onPointerMove={onPointerMove}
          onPointerDown={onPointerDown}
          onPointerUp={onPointerUp}
        />

        {/* HUD 覆盖在画布之上；pointer-events-none，不抢瞄准/发射的指针事件 */}
        <StaHud engine={engine} />

        {/* 品牌字随画布缩放（装饰）；返回钮必须保持真实 44px+ 命中区，
            故移出缩放容器用 floating 变体固定在安全区左上角 */}
        <div className="pointer-events-none absolute inset-x-0 top-0 z-20 flex items-center justify-end p-3">
          <BrandMark slug="shoot-them-all" />
        </div>

        {error ? (
          <div className="absolute inset-0 z-30 flex items-center justify-center bg-black/70 p-6 text-center text-sm text-white/80">
            引擎初始化失败：{error}
          </div>
        ) : null}
      </StaGameShell>
      <GameBackButton variant="floating" />
    </>
  )
}
