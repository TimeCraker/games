"use client"

import dynamic from "next/dynamic"

import { GlobalRuntimeErrorProbe } from "@/src/components/game-shell/GlobalRuntimeErrorProbe"
import { GameRuntimeErrorBoundary } from "@/src/components/game-shell/GameRuntimeErrorBoundary"

const GameEngine = dynamic(() => import("@/src/components/nova-ball/GameEngine").then((m) => m.GameEngine), {
  ssr: false,
  loading: () => <div className="flex min-h-[100dvh] items-center justify-center bg-black text-white/70">加载游戏中…</div>,
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

