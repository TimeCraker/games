"use client"

import dynamic from "next/dynamic"

import { arcadeDisplayName } from "@/src/components/arcade/brand"

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
    <>
      <h1 className="sr-only">{arcadeDisplayName("nebula-survivor")}</h1>
    <GameRuntimeErrorBoundary>
      <NebulaSurvivorGame />
    </GameRuntimeErrorBoundary>
    </>
  )
}
