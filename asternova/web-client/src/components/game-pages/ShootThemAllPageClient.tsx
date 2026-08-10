"use client"

import dynamic from "next/dynamic"

import { GlobalRuntimeErrorProbe } from "@/src/components/game-shell/GlobalRuntimeErrorProbe"
import { GameRuntimeErrorBoundary } from "@/src/components/game-shell/GameRuntimeErrorBoundary"
import { GameLoadingScreen } from "@/src/components/ui/GameLoadingScreen"

const StaRoot = dynamic(() => import("@/src/components/shoot-them-all/StaRoot").then((m) => m.StaRoot), {
  ssr: false,
  loading: () => <GameLoadingScreen label="加载星海" hint="正在准备引擎与资源" />,
})

export function ShootThemAllPageClient() {
  return (
    <>
      <GlobalRuntimeErrorProbe />
      <GameRuntimeErrorBoundary>
        <StaRoot />
      </GameRuntimeErrorBoundary>
    </>
  )
}

