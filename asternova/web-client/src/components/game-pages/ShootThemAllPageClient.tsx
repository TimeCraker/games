"use client"

import dynamic from "next/dynamic"

import { GlobalRuntimeErrorProbe } from "@/src/components/game-shell/GlobalRuntimeErrorProbe"
import { GameRuntimeErrorBoundary } from "@/src/components/game-shell/GameRuntimeErrorBoundary"
import { GameLoadingScreen } from "@/src/components/ui/GameLoadingScreen"

const GameEngine = dynamic(() => import("@/src/components/nova-ball/GameEngine").then((m) => m.GameEngine), {
  ssr: false,
  loading: () => <GameLoadingScreen label="加载游戏中" hint="正在准备引擎与资源" />,
})

export function ShootThemAllPageClient() {
  return (
    <>
      <GlobalRuntimeErrorProbe />
      <GameRuntimeErrorBoundary>
        <GameEngine />
      </GameRuntimeErrorBoundary>
    </>
  )
}

