"use client"

import * as React from "react"
import { Coins, Gem, RotateCcw, Swords } from "lucide-react"

import { CombatCanvas } from "./CombatCanvas"
import { InventoryUI } from "./InventoryUI"
import { ShopUI } from "./ShopUI"
import { CoreDefenseProvider, useCoreDefense } from "./state/coreDefenseContext"

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
    <div className="relative min-h-[100dvh] overflow-hidden bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900 via-[#0a0a0a] to-black text-white">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_30%_0%,rgba(244,114,182,0.2),transparent_40%)]" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_80%_100%,rgba(124,58,237,0.24),transparent_45%)]" />

      <header className="relative z-20 border-b border-white/10 bg-black/25 backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1380px] items-center justify-between px-4 py-3 md:px-6">
          <div>
            <p className="text-[11px] uppercase tracking-[0.3em] text-white/50">AsterNova</p>
            <h1 className="text-xl font-semibold tracking-[-0.02em] md:text-2xl">Core Defense</h1>
          </div>

          <div className="flex items-center gap-2">
            <div className="rounded-2xl border border-amber-200/30 bg-black/35 px-3 py-2 shadow-[0_0_18px_rgba(251,191,36,0.25)]">
              <p className="inline-flex items-center gap-1 text-[11px] text-amber-100/80">
                <Coins className="h-3.5 w-3.5" />
                A-Coin
              </p>
              <p className="text-right text-lg font-bold tabular-nums text-amber-200 drop-shadow-[0_0_10px_rgba(251,191,36,0.6)]">
                {state.gold}
              </p>
            </div>
            <div className="rounded-2xl border border-violet-200/30 bg-black/35 px-3 py-2 shadow-[0_0_18px_rgba(167,139,250,0.28)]">
              <p className="inline-flex items-center gap-1 text-[11px] text-violet-100/80">
                <Gem className="h-3.5 w-3.5" />
                星核碎片
              </p>
              <p className="text-right text-lg font-bold tabular-nums text-violet-200 drop-shadow-[0_0_10px_rgba(196,181,253,0.6)]">
                {state.scrap}
              </p>
            </div>
            <div className="rounded-2xl border border-white/15 bg-black/35 px-3 py-2 text-right">
              <p className="text-[11px] text-white/60">回合 / 波次</p>
              <p className="text-sm font-semibold">
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
            <button
              type="button"
              onClick={() => dispatch({ type: "START_WAVE" })}
              disabled={!state.equipped.length}
              className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-pink-300 to-purple-600 px-5 py-2.5 text-sm font-semibold text-black transition hover:scale-[1.03] hover:shadow-[0_0_24px_rgba(216,180,255,0.7)] disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Swords className="h-4 w-4" />
              Next Wave
            </button>
          ) : null}

          {state.phase === "result" ? (
            <button
              type="button"
              onClick={() => dispatch({ type: "NEXT_ROUND_SETTLEMENT" })}
              className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-pink-300 to-purple-600 px-5 py-2.5 text-sm font-semibold text-black transition hover:scale-[1.03]"
            >
              进入下一回合
            </button>
          ) : null}

          {state.phase === "gameover" ? (
            <button
              type="button"
              onClick={() => dispatch({ type: "RESET_RUN" })}
              className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/[0.08] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-white/[0.14]"
            >
              <RotateCcw className="h-4 w-4" />
              重新开始
            </button>
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
