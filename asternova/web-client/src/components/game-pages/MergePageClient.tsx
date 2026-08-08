"use client"

import dynamic from "next/dynamic"

import { GameRuntimeErrorBoundary } from "@/src/components/game-shell/GameRuntimeErrorBoundary"

const MergeGame = dynamic(() => import("@/src/components/merge/MergeGame").then((m) => m.MergeGame), {
  ssr: false,
  loading: () => <div className="flex min-h-[100dvh] items-center justify-center bg-black text-white/70">加载游戏中…</div>,
})

export function MergePageClient() {
  return (
    <GameRuntimeErrorBoundary>
      <MergeGame />
    </GameRuntimeErrorBoundary>
  )
}

