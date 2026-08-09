"use client"

import * as React from "react"
import { Coins, Gem, RotateCcw, Swords } from "lucide-react"

import { CombatCanvas } from "./CombatCanvas"
import { InventoryUI } from "./InventoryUI"
import { ShopUI } from "./ShopUI"
import { CoreDefenseProvider, useCoreDefense } from "./state/coreDefenseContext"
import { Button } from "@/components/ui/button"

function CoreDefenseScene() {
  const { state, dispatch } = useCoreDefense()
  const [showNotice, setShowNotice] = React.useState(true)

  React.useEffect(() => {
    if (!state.notice) return
    setShowNotice(true)
    const timer = window.setTimeout(() => {
      setShowNotice(false)
      dispatch({ type: "CLEAR_NOTICE" })
    }, 2200)
    return () => window.clearTimeout(timer)
  }, [dispatch, state.notice])

  return (
    <div className="nova-shell-wash relative min-h-dvh overflow-hidden bg-space-black text-white">
      <header className="relative z-20 border-b border-white/10 bg-black/25 backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1380px] items-center justify-between px-4 py-3 md:px-6">
          <div>
            <p className="text-[11px] uppercase tracking-[0.3em] text-white/50">AsterNova</p>
            <h1 className="font-display text-xl font-semibold tracking-[-0.02em] md:text-2xl">Core Defense</h1>
          </div>

          <div className="flex items-center gap-2">
            <div className="rounded-2xl border border-amber-200/30 bg-black/35 px-3 py-2 shadow-sm">
              <p className="inline-flex items-center gap-1 text-[11px] text-amber-100/80">
                <Coins className="h-3.5 w-3.5" />
                A-Coin
              </p>
              <p className="font-mono-data text-right text-lg font-bold text-amber-200">
                {state.gold}
              </p>
            </div>
            <div className="rounded-2xl border border-violet-200/30 bg-black/35 px-3 py-2 shadow-sm">
              <p className="inline-flex items-center gap-1 text-[11px] text-violet-100/80">
                <Gem className="h-3.5 w-3.5" />
                星核碎片
              </p>
              <p className="font-mono-data text-right text-lg font-bold text-violet-200">
                {state.scrap}
              </p>
            </div>
            <div className="rounded-2xl border border-white/15 bg-black/35 px-3 py-2 text-right shadow-sm">
              <p className="text-[11px] text-white/60">回合 / 波次</p>
              <p className="font-mono-data text-sm font-semibold">
                {state.round} / {state.wave}
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="relative z-10 mx-auto flex w-full max-w-[1380px] flex-col gap-4 px-4 py-4 md:px-6">
        {showNotice && state.notice ? (
          <div className="rounded-2xl border border-pink-300/40 bg-pink-500/12 px-4 py-2 text-sm text-pink-100">
            {state.notice}
          </div>
        ) : null}

        {state.phase === "combat" ? (
          <CombatCanvas
            wave={state.wave}
            equipped={state.equipped}
            onCombatEnd={(result) => {
              dispatch({
                type: "SET_COMBAT_RESULT",
                victory: result.victory,
                earnedGold: result.earnedGold,
                earnedScrap: result.earnedScrap,
              })
            }}
          />
        ) : (
          <div className="grid gap-4 xl:grid-cols-[1.45fr_1fr]">
            <ShopUI />
            <InventoryUI />
          </div>
        )}
      </main>

      <div className="pointer-events-none fixed inset-x-0 bottom-0 z-30 flex justify-center bg-gradient-to-t from-black via-black/70 to-transparent pb-4 pt-14">
        <div className="pointer-events-auto flex items-center gap-2">
          {state.phase === "shop" ? (
            <div className="flex flex-col items-center gap-1.5">
              <span className="font-mono-data text-[10px] uppercase tracking-[0.3em] text-white/45">Next Wave</span>
              <Button
                type="button"
                variant="brand"
                onClick={() => dispatch({ type: "START_WAVE" })}
                disabled={!state.equipped.length}
              >
                <Swords className="h-4 w-4" />
                开始下一波
              </Button>
            </div>
          ) : null}

          {state.phase === "result" ? (
            <div className="flex flex-col items-center gap-1.5">
              <span className="font-mono-data text-[10px] uppercase tracking-[0.3em] text-white/45">Next Round</span>
              <Button
                type="button"
                variant="brand"
                onClick={() => dispatch({ type: "NEXT_ROUND_SETTLEMENT" })}
              >
                进入下一回合
              </Button>
            </div>
          ) : null}

          {state.phase === "gameover" ? (
            <div className="flex flex-col items-center gap-1.5">
              <span className="font-mono-data text-[10px] uppercase tracking-[0.3em] text-white/45">Restart</span>
              <Button
                type="button"
                variant="outline"
                onClick={() => dispatch({ type: "RESET_RUN" })}
              >
                <RotateCcw className="h-4 w-4" />
                重新开始
              </Button>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}

export function CoreDefenseGame() {
  return (
    <CoreDefenseProvider>
      <CoreDefenseScene />
    </CoreDefenseProvider>
  )
}
