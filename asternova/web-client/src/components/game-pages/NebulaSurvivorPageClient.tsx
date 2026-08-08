"use client"

import dynamic from "next/dynamic"

import { GameRuntimeErrorBoundary } from "@/src/components/game-shell/GameRuntimeErrorBoundary"

const NebulaSurvivorGame = dynamic(
  () => import("@/src/components/nebula-survivor/NebulaSurvivorGame").then((m) => m.NebulaSurvivorGame),
  {
    ssr: false,
    loading: () => <div className="flex min-h-[100dvh] items-center justify-center bg-black text-white/70">加载游戏中…</div>,
  },
)

export function NebulaSurvivorPageClient() {
  return (
    <GameRuntimeErrorBoundary>
      <NebulaSurvivorGame />
    </GameRuntimeErrorBoundary>
  )
}

