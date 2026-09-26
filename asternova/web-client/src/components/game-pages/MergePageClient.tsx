"use client"

import dynamic from "next/dynamic"

import { arcadeDisplayName } from "@/src/components/arcade/brand"

import { GameRuntimeErrorBoundary } from "@/src/components/game-shell/GameRuntimeErrorBoundary"
import { GameLoadingScreen } from "@/src/components/ui/GameLoadingScreen"

const MergeGame = dynamic(() => import("@/src/components/merge/MergeGame").then((m) => m.MergeGame), {
  ssr: false,
  loading: () => <GameLoadingScreen label="加载游戏中" hint="正在准备引擎与资源" />,
})

export function MergePageClient() {
  return (
    <>
      <h1 className="sr-only">{arcadeDisplayName("merge")}</h1>
      <GameRuntimeErrorBoundary>
      <MergeGame />
    </GameRuntimeErrorBoundary>
    </>
  )
}
