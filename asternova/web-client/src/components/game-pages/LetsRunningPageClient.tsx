"use client"

import dynamic from "next/dynamic"

import { GameRuntimeErrorBoundary } from "@/src/components/game-shell/GameRuntimeErrorBoundary"

const StarDashGame = dynamic(() => import("@/src/components/star-dash/StarDashGame").then((m) => m.StarDashGame), {
  ssr: false,
  loading: () => <div className="flex min-h-[100dvh] items-center justify-center bg-black text-white/70">加载游戏中…</div>,
})

export function LetsRunningPageClient() {
  return (
    <GameRuntimeErrorBoundary>
      <StarDashGame />
    </GameRuntimeErrorBoundary>
  )
}

