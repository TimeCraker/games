"use client"

import dynamic from "next/dynamic"

import { GameRuntimeErrorBoundary } from "@/src/components/game-shell/GameRuntimeErrorBoundary"
import { GameLoadingScreen } from "@/src/components/ui/GameLoadingScreen"

const NebulaSurvivorGame = dynamic(
  () => import("@/src/components/nebula-survivor/NebulaSurvivorGame").then((m) => m.NebulaSurvivorGame),
  {
    ssr: false,
    loading: () => <GameLoadingScreen label="加载游戏中" hint="正在准备引擎与资源" />,
  },
)

export function NebulaSurvivorPageClient() {
  return (
    <GameRuntimeErrorBoundary>
      <NebulaSurvivorGame />
    </GameRuntimeErrorBoundary>
  )
}

