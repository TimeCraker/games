"use client"

/**
 * Nebula Survivor — React 外壳：Canvas + 摇杆 + Apple 风升级卡 / 结算
 */

import * as React from "react"
import { useRouter } from "next/navigation"
import { AnimatePresence, motion } from "framer-motion"
import { NebulaEngine, type UpgradeOffer } from "./nebulaEngine"
import { LoopingBgmControl } from "@/src/components/audio/LoopingBgmControl"

const NEBULA_STORAGE_SKIP_RULES = "nebula-survivor-skip-rules"

type RulesModalKind = "briefing" | "pause" | "reference"

function NebulaIconMove({ className }: { className?: string }) {
  return (
    <span
      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-300/35 to-violet-500/28 ${className ?? ""}`}
      aria-hidden
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-white">
        <path
          d="M12 5v6M9 8l3-3 3 3M5 14h14M8 18h8"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  )
}

function NebulaIconLaser({ className }: { className?: string }) {
  return (
    <span
      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-pink-300/38 to-fuchsia-600/28 ${className ?? ""}`}
      aria-hidden
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-white">
        <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.4" />
        <path d="M12 3v3M12 18v3M3 12h3M18 12h3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      </svg>
    </span>
  )
}

function NebulaIconEye({ className }: { className?: string }) {
  return (
    <span
      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-300/35 to-indigo-700/25 ${className ?? ""}`}
      aria-hidden
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-white">
        <path
          d="M2 12s4-6 10-6 10 6 10 6-4 6-10 6S2 12 2 12Z"
          stroke="currentColor"
          strokeWidth="1.45"
          strokeLinejoin="round"
        />
        <circle cx="12" cy="12" r="2.5" stroke="currentColor" strokeWidth="1.35" />
      </svg>
    </span>
  )
}

function NebulaIconHeart({ className }: { className?: string }) {
  return (
    <span
      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-300/35 to-teal-600/25 ${className ?? ""}`}
      aria-hidden
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className="text-white">
        <path
          d="M12 20s-7-4.35-7-10a4.5 4.5 0 0 1 8.5-2 4.5 4.5 0 0 1 8.5 2c0 5.65-7 10-7 10Z"
          stroke="currentColor"
          strokeWidth="1.4"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  )
}

function useKeyboardMove(set: (x: number, y: number) => void) {
  const keys = React.useRef<Record<string, boolean>>({})

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      keys.current[e.code] = true
      if (["Space", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.code)) e.preventDefault()
    }
    const up = (e: KeyboardEvent) => {
      keys.current[e.code] = false
    }
    const tick = () => {
      let x = 0
      let y = 0
      if (keys.current["KeyW"] || keys.current["ArrowUp"]) y -= 1
      if (keys.current["KeyS"] || keys.current["ArrowDown"]) y += 1
      if (keys.current["KeyA"] || keys.current["ArrowLeft"]) x -= 1
      if (keys.current["KeyD"] || keys.current["ArrowRight"]) x += 1
      set(x, y)
      raf = requestAnimationFrame(tick)
    }
    let raf = requestAnimationFrame(tick)
    window.addEventListener("keydown", down)
    window.addEventListener("keyup", up)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener("keydown", down)
      window.removeEventListener("keyup", up)
    }
  }, [set])
}

function VirtualJoystick({
  onMove,
  disabled,
}: {
  onMove: (x: number, y: number) => void
  disabled: boolean
}) {
  const baseRef = React.useRef<HTMLDivElement>(null)
  const stickRef = React.useRef<HTMLDivElement>(null)
  const dragging = React.useRef(false)
  const radius = 56

  const apply = React.useCallback(
    (clientX: number, clientY: number) => {
      const el = baseRef.current
      if (!el) return
      const r = el.getBoundingClientRect()
      const cx = r.left + r.width / 2
      const cy = r.top + r.height / 2
      let dx = clientX - cx
      let dy = clientY - cy
      const d = Math.hypot(dx, dy) || 1
      const max = radius - 8
      if (d > max) {
        dx = (dx / d) * max
        dy = (dy / d) * max
      }
      if (stickRef.current) {
        stickRef.current.style.transform = `translate(${dx}px, ${dy}px)`
      }
      const nx = d > 4 ? dx / max : 0
      const ny = d > 4 ? dy / max : 0
      onMove(nx, ny)
    },
    [onMove],
  )

  const end = React.useCallback(() => {
    dragging.current = false
    if (stickRef.current) stickRef.current.style.transform = "translate(0,0)"
    onMove(0, 0)
  }, [onMove])

  return (
    <div
      ref={baseRef}
      className={`pointer-events-auto absolute bottom-[max(1rem,env(safe-area-inset-bottom))] left-[max(0.75rem,env(safe-area-inset-left))] z-20 flex h-[120px] w-[120px] items-center justify-center rounded-full border-[0.5px] border-white/[0.14] bg-black/25 shadow-[0_8px_40px_rgba(0,0,0,0.45),inset_0_1px_0_rgba(255,255,255,0.06)] backdrop-blur-xl sm:bottom-8 sm:left-8 sm:h-[132px] sm:w-[132px] ${disabled ? "pointer-events-none opacity-35" : "touch-none"}`}
      style={{ WebkitBackdropFilter: "blur(20px)" }}
      onPointerDown={(e) => {
        if (disabled) return
        e.preventDefault()
        dragging.current = true
        baseRef.current?.setPointerCapture(e.pointerId)
        apply(e.clientX, e.clientY)
      }}
      onPointerMove={(e) => {
        if (!dragging.current || disabled) return
        apply(e.clientX, e.clientY)
      }}
      onPointerUp={end}
      onPointerCancel={end}
    >
      <div className="pointer-events-none absolute inset-2 rounded-full bg-gradient-to-br from-fuchsia-500/10 to-violet-600/5" />
      <div
        ref={stickRef}
        className="pointer-events-none relative h-12 w-12 rounded-full border-[0.5px] border-white/25 bg-gradient-to-br from-pink-300/35 to-violet-500/30 shadow-[0_0_24px_rgba(236,72,153,0.25)]"
      />
    </div>
  )
}

function UpgradeCard({
  offer,
  onPick,
  index,
}: {
  offer: UpgradeOffer
  onPick: () => void
  index: number
}) {
  const accent =
    offer.trackId === "fire_salvo" || offer.trackId === "fire_rate"
      ? "from-pink-400/35 via-rose-400/20 to-fuchsia-600/25"
      : offer.trackId === "ring_count" || offer.trackId === "ring_spin"
        ? "from-violet-400/35 via-purple-500/22 to-indigo-700/25"
        : "from-cyan-400/30 via-sky-500/22 to-blue-700/28"

  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, y: 28, scale: 0.94 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: 0.08 * index, type: "spring", stiffness: 320, damping: 26 }}
      onClick={onPick}
      className="group relative w-full max-w-[280px] overflow-hidden rounded-[1.35rem] border-[0.5px] border-white/[0.18] bg-white/[0.07] text-left shadow-[0_1px_0_rgba(255,255,255,0.07)_inset,0_24px_80px_rgba(0,0,0,0.55),0_0_0_1px_rgba(255,255,255,0.04)] backdrop-blur-2xl transition hover:border-white/25 hover:bg-white/[0.09] active:scale-[0.99] sm:max-w-none"
      style={{ WebkitBackdropFilter: "blur(28px) saturate(160%)" }}
    >
      <div className={`pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-gradient-to-br ${accent} opacity-90 blur-2xl`} />
      <div className="relative p-4 sm:p-5">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-white/40">Upgrade</p>
            <h3 className="mt-1.5 text-lg font-semibold tracking-tight text-white sm:text-xl">{offer.title}</h3>
          </div>
          <span className="shrink-0 rounded-full border-[0.5px] border-white/15 bg-black/30 px-2.5 py-1 text-[11px] font-medium tabular-nums text-white/55">
            {offer.badgeLabel === "MAX" ? "MAX" : offer.badgeLabel}
          </span>
        </div>
        <p className="mt-3 text-[13px] leading-relaxed text-white/55">{offer.desc}</p>
        <div className="mt-4 flex items-center justify-between gap-2">
          <span className="text-[11px] text-fuchsia-200/70">
            {offer.isNew ? "新能力" : "强化"}
          </span>
          <span className="rounded-full bg-gradient-to-r from-pink-400/85 via-fuchsia-500/80 to-violet-500/85 px-4 py-1.5 text-[12px] font-semibold text-gray-950 shadow-lg shadow-fuchsia-500/15">
            选取
          </span>
        </div>
      </div>
    </motion.button>
  )
}

export function NebulaSurvivorGame() {
  const router = useRouter()
  const canvasRef = React.useRef<HTMLCanvasElement>(null)
  const engineRef = React.useRef<NebulaEngine | null>(null)
  const rafRef = React.useRef<number>(0)
  const lastRef = React.useRef<number>(0)

  const joyRef = React.useRef({ x: 0, y: 0 })
  const joyMove = React.useCallback((x: number, y: number) => {
    joyRef.current = { x, y }
  }, [])

  const keyRef = React.useRef({ x: 0, y: 0 })
  const keySet = React.useCallback((x: number, y: number) => {
    keyRef.current = { x, y }
  }, [])
  useKeyboardMove(keySet)

  const [rulesModalOpen, setRulesModalOpen] = React.useState(true)
  const [rulesModalKind, setRulesModalKind] = React.useState<RulesModalKind>("briefing")
  const [dontShowRulesAgain, setDontShowRulesAgain] = React.useState(false)

  const rulesOpenRef = React.useRef(rulesModalOpen)
  const rulesKindRef = React.useRef(rulesModalKind)

  React.useLayoutEffect(() => {
    rulesOpenRef.current = rulesModalOpen
    rulesKindRef.current = rulesModalKind
  }, [rulesModalOpen, rulesModalKind])

  const [ui, setUi] = React.useState({
    score: 0,
    kills: 0,
    hp: 82,
    maxHp: 82,
    level: 1,
    xp: 0,
    xpToNext: 32,
    worldTier: 1,
    pausedUpgrade: false,
    choices: [] as UpgradeOffer[],
    upgradeRerollsLeft: 0,
    gameOver: false,
  })

  const syncUi = React.useCallback(() => {
    const g = engineRef.current
    if (!g) return
    setUi({
      score: g.score,
      kills: g.kills,
      hp: g.player.hp,
      maxHp: g.player.maxHp,
      level: g.player.level,
      xp: g.player.xp,
      xpToNext: g.player.xpToNext,
      worldTier: g.worldDifficultyTier(),
      pausedUpgrade: g.pausedUpgrade,
      choices: g.upgradeChoices,
      upgradeRerollsLeft: g.upgradeRerollsLeft,
      gameOver: g.gameOver,
    })
  }, [])

  React.useLayoutEffect(() => {
    try {
      if (localStorage.getItem(NEBULA_STORAGE_SKIP_RULES) === "1") setRulesModalOpen(false)
    } catch {
      /* ignore */
    }
  }, [])

  React.useLayoutEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const g = new NebulaEngine()
    engineRef.current = g

    const resize = () => {
      const dpr = Math.min(2, window.devicePixelRatio || 1)
      const rect = canvas.getBoundingClientRect()
      const lw = Math.max(280, Math.floor(rect.width))
      const lh = Math.max(360, Math.floor(rect.height))
      canvas.width = Math.floor(lw * dpr)
      canvas.height = Math.floor(lh * dpr)
      canvas.style.width = `${lw}px`
      canvas.style.height = `${lh}px`
      g.w = canvas.width
      g.h = canvas.height
      g.dpr = dpr
    }

    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(canvas.parentElement ?? canvas)

    let uiAcc = 0
    const loop = (t: number) => {
      const g = engineRef.current
      if (!g) return
      const prev = lastRef.current
      lastRef.current = t
      const raw = prev ? (t - prev) / 1000 : 1 / 60
      const dt = Math.min(0.05, Math.max(1 / 240, raw))

      let mx = keyRef.current.x + joyRef.current.x
      let my = keyRef.current.y + joyRef.current.y
      const m = Math.hypot(mx, my)
      if (m > 1) {
        mx /= m
        my /= m
      }
      g.moveX = mx
      g.moveY = my

      const prevPause = g.pausedUpgrade
      const prevOver = g.gameOver
      g.update(dt)
      const ctx = canvas.getContext("2d")
      if (ctx) g.render(ctx)

      uiAcc += dt
      if (uiAcc >= 0.1 || g.pausedUpgrade !== prevPause || g.gameOver !== prevOver) {
        uiAcc = 0
        syncUi()
      }
      rafRef.current = requestAnimationFrame(loop)
    }
    rafRef.current = requestAnimationFrame(loop)
    syncUi()

    return () => {
      cancelAnimationFrame(rafRef.current)
      ro.disconnect()
      engineRef.current = null
      lastRef.current = 0
    }
  }, [syncUi])

  React.useLayoutEffect(() => {
    const g = engineRef.current
    if (g) g.rulesFrozen = rulesModalOpen
  }, [rulesModalOpen])

  const closeRulesPrimary = React.useCallback(() => {
    if (rulesModalKind === "briefing") {
      try {
        if (dontShowRulesAgain) localStorage.setItem(NEBULA_STORAGE_SKIP_RULES, "1")
      } catch {
        /* ignore */
      }
    }
    setRulesModalOpen(false)
  }, [dontShowRulesAgain, rulesModalKind])

  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.code !== "Escape" && e.code !== "KeyP") return
      const eng = engineRef.current
      if (!eng || eng.gameOver || eng.pausedUpgrade) return

      if (rulesOpenRef.current) {
        const k = rulesKindRef.current
        if (k === "pause" || k === "reference") {
          e.preventDefault()
          setRulesModalOpen(false)
        }
        return
      }
      e.preventDefault()
      setRulesModalKind("pause")
      setRulesModalOpen(true)
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [])

  const onCanvasMove = React.useCallback(
    (e: React.PointerEvent<HTMLCanvasElement>) => {
      const g = engineRef.current
      const c = canvasRef.current
      if (!g || !c) return
      const r = c.getBoundingClientRect()
      const lx = e.clientX - r.left
      const ly = e.clientY - r.top
      g.mouseWorldX = g.player.x + (lx - r.width / 2)
      g.mouseWorldY = g.player.y + (ly - r.height / 2)
    },
    [],
  )

  const restart = React.useCallback(() => {
    const g = engineRef.current
    if (!g) return
    g.reset()
    lastRef.current = 0
    syncUi()
  }, [syncUi])

  const blocked = rulesModalOpen || ui.pausedUpgrade || ui.gameOver

  return (
    <div
      className="relative flex h-full min-h-0 min-h-full flex-col overflow-hidden bg-[#05040a] text-white"
      style={{ fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif' }}
    >
      <div className="relative z-10 flex shrink-0 items-center justify-between gap-2 border-b border-white/[0.07] px-3 py-2.5 backdrop-blur-xl sm:px-5 sm:py-3">
        <button
          type="button"
          onClick={() => router.push("/lobby")}
          className="rounded-full border-[0.5px] border-white/15 bg-white/[0.06] px-3 py-1.5 text-[12px] font-medium text-white/85 sm:px-4 sm:py-2 sm:text-sm"
        >
          大厅
        </button>
        <div className="text-center">
          <div className="text-[10px] font-medium uppercase tracking-[0.2em] text-white/35">AsterNova</div>
          <div className="bg-gradient-to-r from-pink-200 via-fuchsia-200 to-violet-300 bg-clip-text text-sm font-semibold text-transparent sm:text-base">
            Nebula Survivor
          </div>
        </div>
        <div className="flex items-center gap-1.5 sm:gap-2">
          <button
            type="button"
            title="暂停（战斗中按 P 亦可）"
            disabled={ui.gameOver || ui.pausedUpgrade || rulesModalOpen}
            onClick={() => {
              setRulesModalKind("pause")
              setRulesModalOpen(true)
            }}
            className="rounded-full border-[0.5px] border-white/15 bg-white/[0.06] px-2 py-1 text-[11px] font-medium text-white/75 disabled:pointer-events-none disabled:opacity-35 sm:px-2.5 sm:text-xs"
          >
            暂停
          </button>
          <button
            type="button"
            disabled={rulesModalOpen}
            onClick={() => {
              setRulesModalKind("reference")
              setRulesModalOpen(true)
            }}
            className="rounded-full border-[0.5px] border-white/15 bg-white/[0.06] px-2.5 py-1 text-[11px] font-medium text-white/75 disabled:pointer-events-none disabled:opacity-35 sm:px-3 sm:text-xs"
          >
            规则
          </button>
          <div className="text-right text-[11px] tabular-nums text-white/50 sm:text-xs">
            <div>击杀 {ui.kills}</div>
            <div className="text-white/70">分 {ui.score}</div>
          </div>
        </div>
      </div>

      <div className="relative min-h-0 flex-1">
        <div className="pointer-events-none absolute left-3 top-2 z-10 flex flex-col gap-2 rounded-2xl border-[0.5px] border-white/[0.1] bg-black/35 px-3 py-2 text-[11px] shadow-lg backdrop-blur-md sm:left-5 sm:top-4 sm:text-xs">
          <div className="flex items-center gap-2">
            <span className="w-5 shrink-0 text-right text-[10px] font-semibold tracking-wide text-white/50 sm:text-[11px]">
              HP
            </span>
            <div className="relative h-2 w-[6.5rem] shrink-0 overflow-hidden rounded-full border border-white/[0.07] bg-gradient-to-b from-black/55 to-black/80 shadow-[inset_0_2px_5px_rgba(0,0,0,0.72),inset_0_-1px_0_rgba(255,255,255,0.04)] sm:w-36">
              <div
                className="relative h-full rounded-full bg-gradient-to-b from-fuchsia-300/95 via-pink-500 to-violet-900 shadow-[inset_0_1px_0_rgba(255,255,255,0.42),inset_0_-3px_6px_rgba(0,0,0,0.35)] transition-[width] duration-150 ease-out"
                style={{ width: `${Math.max(0, Math.min(100, (ui.hp / ui.maxHp) * 100))}%` }}
              >
                <span className="pointer-events-none absolute left-[12%] right-[12%] top-px h-px rounded-full bg-white/35 blur-[0.5px]" />
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-5 shrink-0 text-right text-[10px] font-semibold tracking-wide text-emerald-200/55 sm:text-[11px]">
              XP
            </span>
            <div className="relative h-2 w-[6.5rem] shrink-0 overflow-hidden rounded-full border border-emerald-950/40 bg-gradient-to-b from-black/55 to-black/80 shadow-[inset_0_2px_5px_rgba(0,0,0,0.72),inset_0_-1px_0_rgba(52,211,153,0.06)] sm:w-36">
              <div
                className="relative h-full min-w-0 rounded-full bg-gradient-to-b from-[#b8ffd9] via-[#34d399] to-[#065f46] shadow-[inset_0_1px_0_rgba(255,255,255,0.55),inset_0_-3px_8px_rgba(0,40,30,0.45),0_0_12px_rgba(52,211,153,0.22)] transition-[width] duration-150 ease-out"
                style={{
                  width: `${Math.max(0, Math.min(100, ui.xpToNext > 0 ? (ui.xp / ui.xpToNext) * 100 : 100))}%`,
                }}
              >
                <span className="pointer-events-none absolute left-[10%] right-[10%] top-px h-[2px] rounded-full bg-gradient-to-r from-transparent via-white/50 to-transparent opacity-90" />
                <span className="pointer-events-none absolute bottom-0 left-0 right-0 h-px bg-black/25" />
              </div>
            </div>
          </div>
          <div className="text-white/55">
            Lv.{ui.level}
            <span className="text-white/35">
              {" "}
              · {Math.floor(ui.xp)}/{ui.xpToNext}
            </span>
          </div>
          <div className="text-[10px] text-white/40">波次 {ui.worldTier} · 约每分钟升一档</div>
          <div className="text-[9px] leading-tight text-emerald-200/50">青绿光球+十字为急救包（极稀有）</div>
        </div>

        <canvas
          ref={canvasRef}
          className={`block h-full w-full min-h-[240px] touch-none ${blocked ? "pointer-events-none" : ""}`}
          onPointerMove={onCanvasMove}
          onPointerEnter={() => {
            const g = engineRef.current
            if (g) g.useMouseMove = true
          }}
          onPointerLeave={() => {
            const g = engineRef.current
            if (g) g.useMouseMove = false
          }}
        />

        <VirtualJoystick onMove={joyMove} disabled={blocked} />

        <p className="pointer-events-none absolute bottom-[max(0.35rem,env(safe-area-inset-bottom))] right-2 z-10 max-w-[12rem] text-[9px] leading-snug text-white/35 sm:bottom-3 sm:right-5 sm:max-w-none sm:text-[10px]">
          WASD / 方向键 · 指针滑移 · 左下摇杆 · <span className="text-white/45">P 暂停</span>（暂停时见规则）
        </p>
      </div>

      {rulesModalOpen ? (
        <div
          className="fixed inset-0 z-[45] flex items-end justify-center bg-black/58 backdrop-blur-md sm:items-center sm:p-5"
          role="dialog"
          aria-modal="true"
          aria-labelledby="nebula-rules-title"
          style={{
            paddingLeft: "max(0.75rem, env(safe-area-inset-left, 0px))",
            paddingRight: "max(0.75rem, env(safe-area-inset-right, 0px))",
            paddingBottom: "max(0.75rem, env(safe-area-inset-bottom, 0px))",
            paddingTop: "max(0.5rem, env(safe-area-inset-top, 0px))",
          }}
        >
          <div
            className="max-h-[min(90dvh,720px)] w-full max-w-[440px] overflow-y-auto overscroll-contain rounded-t-[1.5rem] border-[0.5px] border-white/[0.12] border-b-0 bg-white/[0.07] p-4 shadow-[0_28px_90px_rgba(0,0,0,0.6)] backdrop-blur-2xl sm:rounded-[2rem] sm:border-b sm:p-6"
            style={{ WebkitBackdropFilter: "blur(28px) saturate(165%)" }}
          >
            <p className="text-center text-[10px] font-semibold uppercase tracking-[0.26em] text-white/38">Briefing</p>
            {rulesModalKind === "pause" ? (
              <div className="mt-2 flex justify-center">
                <span className="rounded-full border border-amber-200/25 bg-amber-400/15 px-3 py-1 text-[11px] font-semibold tracking-wide text-amber-100/95">
                  已暂停
                </span>
              </div>
            ) : null}
            <h2 id="nebula-rules-title" className="mt-1.5 text-center text-xl font-semibold tracking-tight text-white sm:text-2xl">
              Nebula Survivor
            </h2>
            <p className="mt-1 text-center text-[12px] text-white/45">
              {rulesModalKind === "briefing"
                ? "读完后点击「开始任务」进入战场"
                : rulesModalKind === "pause"
                  ? "游戏已暂停 · 可复习下方规则，关闭后继续战斗（Esc / P 亦可关闭）"
                  : "查阅完毕后点击下方按钮返回游戏"}
            </p>

            <ul className="mt-5 space-y-3.5 text-[13px] leading-relaxed text-white/78">
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <NebulaIconMove />
                <div>
                  <div className="font-medium text-white/95">移动</div>
                  <div className="mt-0.5 text-[12px] text-white/52">
                    <span className="text-cyan-200/85">WASD / 方向键</span>，指针在画面上可向鼠标方向滑移；手机用左下摇杆。
                  </div>
                </div>
              </li>
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <NebulaIconLaser />
                <div>
                  <div className="font-medium text-white/95">火力覆盖</div>
                  <div className="mt-0.5 text-[12px] text-white/52">
                    粉红弹幕仅在<span className="text-pink-200/85">视野相近范围</span>内锁定最近敌人；可分别强化<span className="text-pink-200/85">齐射发数</span>与<span className="text-pink-200/85">射速</span>。
                  </div>
                </div>
              </li>
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <NebulaIconEye />
                <div>
                  <div className="font-medium text-white/95">敌人察觉</div>
                  <div className="mt-0.5 text-[12px] text-white/52">
                    屏外敌人会先<span className="text-violet-200/85">短暂靠近再游荡</span>；一旦<span className="text-violet-200/85">出现在视野内</span>或<span className="text-violet-200/85">进入察觉范围</span>即持续追击。最小档有暖色外圈描边。
                  </div>
                </div>
              </li>
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <NebulaIconHeart />
                <div>
                  <div className="font-medium text-white/95">升级与急救</div>
                  <div className="mt-0.5 text-[12px] text-white/52">
                    五条强化（火力弹幕/射速、星环数量/转速、推进器）中<span className="text-violet-200/85">随机三选一</span>，每级可<span className="text-violet-200/85">免费刷新一次</span>。击杀<span className="text-emerald-200/85">极低概率</span>掉急救包。
                  </div>
                </div>
              </li>
            </ul>

            {rulesModalKind === "briefing" ? (
              <label className="mt-4 flex cursor-pointer items-center gap-3 rounded-2xl border border-white/[0.08] bg-white/[0.04] px-3 py-2.5 text-[12px] text-white/68">
                <input
                  type="checkbox"
                  checked={dontShowRulesAgain}
                  onChange={(e) => setDontShowRulesAgain(e.target.checked)}
                  className="h-4 w-4 rounded-md border-white/30 bg-white/10 text-teal-500 focus:ring-teal-400/50"
                />
                下次不再显示（本机记住）
              </label>
            ) : null}

            <button
              type="button"
              onClick={closeRulesPrimary}
              className="mt-4 w-full rounded-2xl bg-gradient-to-r from-pink-400/90 via-fuchsia-500/88 to-violet-600/88 py-3.5 text-[15px] font-semibold text-gray-950 shadow-lg shadow-fuchsia-500/18"
            >
              {rulesModalKind === "briefing" ? "开始任务" : rulesModalKind === "pause" ? "继续游戏" : "返回游戏"}
            </button>
          </div>
        </div>
      ) : null}

      <AnimatePresence>
        {ui.pausedUpgrade && ui.choices.length > 0 ? (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-3 backdrop-blur-xl sm:p-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              paddingTop: "max(0.75rem, env(safe-area-inset-top))",
              paddingBottom: "max(0.75rem, env(safe-area-inset-bottom))",
            }}
          >
            <motion.div
              initial={{ scale: 0.96, y: 16 }}
              animate={{ scale: 1, y: 0 }}
              className="max-h-[92dvh] w-full max-w-[920px] overflow-y-auto rounded-[1.75rem] border-[0.5px] border-white/[0.12] bg-white/[0.06] p-4 shadow-[0_32px_100px_rgba(0,0,0,0.65),inset_0_1px_0_rgba(255,255,255,0.06)] sm:rounded-[2rem] sm:p-8"
              style={{ WebkitBackdropFilter: "blur(32px) saturate(170%)" }}
            >
              <p className="text-center text-[10px] font-semibold uppercase tracking-[0.28em] text-white/40">Time Stop</p>
              <h2 className="mt-2 text-center text-xl font-semibold tracking-tight text-white sm:text-2xl">选择一项升级</h2>
              <p className="mx-auto mt-1 max-w-md text-center text-[13px] text-white/45">
                五条强化中随机三张 · 每级可免费<span className="text-white/60">刷新一次</span>换一批 · 必须选一项后继续
              </p>
              <div className="mt-4 flex flex-col items-center gap-2 sm:mt-5">
                <button
                  type="button"
                  disabled={ui.upgradeRerollsLeft < 1}
                  onClick={() => {
                    const eng = engineRef.current
                    if (!eng || !eng.rerollUpgradeChoices()) return
                    syncUi()
                  }}
                  className="rounded-full border-[0.5px] border-white/18 bg-white/[0.07] px-5 py-2 text-[12px] font-medium text-white/85 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] backdrop-blur-md transition hover:border-white/25 hover:bg-white/[0.1] disabled:pointer-events-none disabled:opacity-35"
                >
                  {ui.upgradeRerollsLeft >= 1 ? "刷新三选一（本局仅此一次）" : "已使用过刷新"}
                </button>
              </div>
              <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-3 sm:gap-5">
                {ui.choices.map((c, i) => (
                  <UpgradeCard
                    key={`${c.trackId}-${i}`}
                    offer={c}
                    index={i}
                    onPick={() => {
                      const eng = engineRef.current
                      if (!eng) return
                      eng.pickUpgrade(c)
                      syncUi()
                    }}
                  />
                ))}
              </div>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <AnimatePresence>
        {ui.gameOver ? (
          <motion.div
            className="fixed inset-0 z-[60] flex items-center justify-center bg-black/65 p-5 backdrop-blur-md"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.94, y: 12 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              className="w-full max-w-md rounded-[1.75rem] border-[0.5px] border-white/[0.15] bg-white/[0.08] p-7 text-center shadow-[0_24px_90px_rgba(0,0,0,0.55)] backdrop-blur-2xl"
              style={{ WebkitBackdropFilter: "blur(26px)" }}
            >
              <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-white/40">Mission End</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">信号丢失</h2>
              <p className="mt-2 text-[13px] text-white/50">暗物质潮淹没宇航服护盾</p>
              <p className="mt-6 text-4xl font-semibold tabular-nums text-white">{ui.score}</p>
              <p className="text-[12px] text-white/40">本局得分 · 击杀 {ui.kills}</p>
              <div className="mt-6 flex flex-col gap-2">
                <button
                  type="button"
                  onClick={restart}
                  className="w-full rounded-2xl bg-gradient-to-r from-pink-400 via-fuchsia-500 to-violet-600 py-3.5 text-[15px] font-semibold text-gray-950 shadow-lg shadow-fuchsia-500/20"
                >
                  再闯星云
                </button>
                <button
                  type="button"
                  onClick={() => router.push("/lobby")}
                  className="w-full rounded-2xl border-[0.5px] border-white/15 bg-white/5 py-3 text-[14px] font-medium text-white/80"
                >
                  返回大厅
                </button>
              </div>
              <p className="mt-6 text-[12px] italic text-violet-200/75">Reach Beyond the Stars</p>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
      <LoopingBgmControl src="/audio/games/nebula-survivor/Untitled.mp3" storageKey="bgm-volume:nebula-survivor" />
    </div>
  )
}
