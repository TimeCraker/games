"use client"

import * as React from "react"

import { HEIGHT, WIDTH } from "./constants"

/**
 * 纵向游戏外壳（Stage Spec §8.10，新建 StaGameShell）。
 *
 * 现有 MobileLandscapeGameShell 桌面分支不走等比缩放，纵向 720×1280 在桌面会失真。
 * 本壳在桌面与移动端都做居中等比缩放（min(vw/W, vh/H)），
 * 两侧/上下留黑填充氛围星云渐变（gutter），后续可挂侧栏 HUD 槽。
 */
export function StaGameShell({ children }: { children: React.ReactNode }) {
  const [scale, setScale] = React.useState(1)

  React.useEffect(() => {
    const update = () => {
      const vw = window.visualViewport?.width ?? window.innerWidth
      const vh = window.visualViewport?.height ?? window.innerHeight
      const s = Math.min(vw / WIDTH, vh / HEIGHT)
      setScale(Number.isFinite(s) && s > 0 ? s : 1)
    }
    update()
    window.addEventListener("resize", update)
    window.addEventListener("orientationchange", update)
    window.visualViewport?.addEventListener("resize", update)
    return () => {
      window.removeEventListener("resize", update)
      window.removeEventListener("orientationchange", update)
      window.visualViewport?.removeEventListener("resize", update)
    }
  }, [])

  return (
    <div
      className="relative overflow-hidden"
      style={{
        width: "100vw",
        height: "100dvh",
        touchAction: "none",
        userSelect: "none",
        WebkitUserSelect: "none",
        WebkitTouchCallout: "none",
        overscrollBehavior: "none",
        background:
          "radial-gradient(ellipse 60% 50% at 50% 25%, rgba(56,107,255,0.12), transparent 70%)," +
          "radial-gradient(ellipse 45% 45% at 50% 85%, rgba(168,85,247,0.10), transparent 70%)," +
          "#04050c",
      }}
    >
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          width: `${WIDTH}px`,
          height: `${HEIGHT}px`,
          transform: `translate(-50%, -50%) scale(${scale})`,
          transformOrigin: "center center",
          overflow: "hidden",
        }}
      >
        {children}
      </div>
    </div>
  )
}
