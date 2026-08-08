"use client"

import * as React from "react"
import { useMobileGameViewport } from "@/src/hooks/useMobileGameViewport"
import { ScaleFitGameStage } from "@/src/components/game-shell/ScaleFitGameStage"

type Props = {
  children: React.ReactNode
  designWidth?: number
  designHeight?: number
}

/**
 * 统一自适应容器：
 * - 不再强制横屏、不做旋转壳
 * - 手机端使用固定设计尺寸舞台 + 等比缩放
 */
export function MobileLandscapeGameShell({ children, designWidth = 1280, designHeight = 720 }: Props) {
  const { isMobile, isPortraitMobile } = useMobileGameViewport()

  if (!isMobile) {
    return (
      <div className="relative min-h-[100dvh] min-h-screen w-full max-w-[100vw] overflow-x-hidden bg-black">
        {children}
      </div>
    )
  }

  return (
    <ScaleFitGameStage defaultWidth={designWidth} defaultHeight={designHeight}>
      <div className="relative h-full w-full bg-black">
        {isPortraitMobile ? (
        <div className="pointer-events-none absolute left-1/2 top-[max(0.5rem,env(safe-area-inset-top))] z-[20] max-w-[92vw] -translate-x-1/2 rounded-full border border-white/12 bg-black/55 px-3 py-1 text-center text-[10px] leading-snug text-white/60 backdrop-blur-md">
          竖屏自适应模式
        </div>
        ) : null}
        <div className="mobile-game-landscape-fill h-full w-full overflow-hidden">{children}</div>
      </div>
    </ScaleFitGameStage>
  )
}
