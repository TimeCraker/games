"use client"

import dynamic from "next/dynamic"

import { GameRuntimeErrorBoundary } from "@/src/components/game-shell/GameRuntimeErrorBoundary"
import { GameLoadingScreen } from "@/src/components/ui/GameLoadingScreen"

const StarDashGame = dynamic(() => import("@/src/components/star-dash/StarDashGame").then((m) => m.StarDashGame), {
  ssr: false,
  loading: () => <GameLoadingScreen label="加载游戏中" hint="正在准备引擎与资源" />,
})

export function LetsRunningPageClient() {
  return (
    <GameRuntimeErrorBoundary>
      <StarDashGame />
    </GameRuntimeErrorBoundary>
  )
}

