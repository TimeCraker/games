"use client"

/**
 * Nebula Survivor — React 外壳：Canvas + 摇杆 + Apple 风升级卡 / 结算
 */

import * as React from "react"
import { AnimatePresence, motion, useMotionTemplate, useMotionValue } from "framer-motion"
import { ArcadeEntry } from "@/src/components/arcade/ArcadeEntry"
import { ArcadeResult } from "@/src/components/arcade/ArcadeResult"
import { arcadeAccentStyle } from "@/src/components/arcade/accent"
import { useArcadeAccent } from "@/src/components/arcade/useArcadeAccent"
import { BrandMark } from "@/src/components/arcade/BrandMark"
import { HudMeter, HudStat, HudTopBar } from "@/src/components/arcade/HudKit"
import { NebulaPixiHost } from "./render/NebulaPixiHost"
import { nebulaSfx } from "./render/NebulaSfx"
import { Volume2, VolumeX } from "lucide-react"
import type { NebulaEngine, UpgradeOffer, UpgradeTrackId } from "./nebulaEngine"
import { LoopingBgmControl } from "@/src/components/audio/LoopingBgmControl"
import { GameBackButton } from "@/src/components/ui/GameBackButton"
import { StagePortal } from "@/src/components/game-shell/StagePortal"
import { useMobileGameViewport } from "@/src/hooks/useMobileGameViewport"

const NEBULA_STORAGE_SKIP_RULES = "nebula-survivor-skip-rules"

type RulesModalKind = "briefing" | "pause" | "reference"

function NebulaIconMove({ className }: { className?: string }) {
  return (
    <span
      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-300/35 to-amber-600/28 ${className ?? ""}`}
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
      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#C08069]/38 to-[#7E4A38]/28 ${className ?? ""}`}
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
      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#8CBEAA]/35 to-[#3F6B58]/25 ${className ?? ""}`}
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
      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#A9C98F]/35 to-[#4F8D6B]/28 ${className ?? ""}`}
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

/** 五条升级轨道的显示元数据（纯视觉，不改平衡） */
const TRACK_META: Record<
  UpgradeTrackId,
  { label: string; cap: number; bar: string; line: string; chip: string }
> = {
  fire_salvo: { label: "弹幕", cap: 6, bar: "from-amber-300 to-amber-600", line: "text-amber-200/80", chip: "bg-amber-400/12 text-amber-100/85" },
  fire_rate: { label: "射速", cap: 6, bar: "from-[#A9C98F] to-[#5F7D42]", line: "text-[#C9E0B4]/80", chip: "bg-[#A9C98F]/12 text-[#DFEDD2]/85" },
  ring_count: { label: "星环", cap: 12, bar: "from-[#8CBEAA] to-[#3F6B58]", line: "text-[#CFE8DE]/80", chip: "bg-[#8CBEAA]/12 text-[#CFE8DE]/85" },
  ring_spin: { label: "环速", cap: 6, bar: "from-[#C08069] to-[#7E4A38]", line: "text-[#E8CBB8]/80", chip: "bg-[#C08069]/12 text-[#E8CBB8]/85" },
  afterburner: { label: "推进", cap: 6, bar: "from-[#A8BED6] to-[#5E7994]", line: "text-[#C6D6E6]/80", chip: "bg-[#A8BED6]/12 text-[#D5E1EC]/85" },
}

function formatTime(sec: number): string {
  const s = Math.max(0, Math.floor(sec))
  const m = Math.floor(s / 60)
  return `${m}:${String(s % 60).padStart(2, "0")}`
}

function TrackGlyph({ id, className }: { id: UpgradeTrackId; className?: string }) {
  const attrs = { fill: "none", stroke: "currentColor", strokeWidth: 1.5, strokeLinecap: "round", strokeLinejoin: "round" } as const
  let inner: React.ReactNode
  if (id === "fire_salvo") inner = <path d="M12 4.5 17 19.5 12 16 7 19.5Z" />
  else if (id === "fire_rate") inner = (<><circle cx="12" cy="12" r="4.1" /><path d="M12 3v3.2M12 17.8V21M3 12h3.2M17.8 12H21" /></>)
  else if (id === "ring_count") inner = (<><circle cx="12" cy="12" r="6.4" /><circle cx="18.4" cy="12" r="2" fill="currentColor" stroke="none" /></>)
  else if (id === "ring_spin") inner = <path d="M12 5.5a6.5 6.5 0 0 1 6.5 6.5M12 18.5a6.5 6.5 0 0 1-6.5-6.5" />
  else inner = <path d="M6.5 17.5 17.5 6.5M13 6.5h4.5V11M11 17.5H6.5V13" />
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" className={className} aria-hidden {...attrs}>
      {inner}
    </svg>
  )
}

/** 遥测盘角括号（可识别签名，非通用圆角卡片） */
function PanelCorners({ className }: { className?: string }) {
  return (
    <>
      <svg className={`pointer-events-none absolute left-1.5 top-1.5 h-3 w-3 ${className ?? "text-hud-accent/70"}`} viewBox="0 0 12 12" fill="none" aria-hidden>
        <path d="M1 11V3.5A2.5 2.5 0 0 1 3.5 1H11" stroke="currentColor" strokeWidth="1.4" />
      </svg>
      <svg className={`pointer-events-none absolute bottom-1.5 right-1.5 h-3 w-3 ${className ?? "text-hud-accent/70"}`} viewBox="0 0 12 12" fill="none" aria-hidden>
        <path d="M11 1v7.5A2.5 2.5 0 0 1 8.5 11H1" stroke="currentColor" strokeWidth="1.4" />
      </svg>
    </>
  )
}

function Pips({ level, max, barClass }: { level: number; max: number; barClass: string }) {
  const shown = Math.min(max, 12)
  return (
    <span className="flex items-center gap-[3px]">
      {Array.from({ length: shown }, (_, i) => (
        <span key={i} className={`h-[3px] w-[3px] rounded-full ${i < level ? "bg-gradient-to-r " + barClass : "bg-white/12"}`} />
      ))}
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
      <div className="pointer-events-none absolute inset-2 rounded-full bg-gradient-to-br from-amber-500/10 to-amber-700/5" />
      <div
        ref={stickRef}
        className="pointer-events-none relative h-12 w-12 rounded-full border-[0.5px] border-white/25 bg-gradient-to-br from-amber-300/35 to-amber-600/30 shadow-[0_0_24px_rgba(216,163,60,0.25)]"
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
  const meta = TRACK_META[offer.trackId]
  const cap = meta.cap
  const parsed = /(\d+)\/(\d+)/.exec(offer.badgeLabel)
  const cur = offer.badgeLabel === "MAX" ? cap : parsed ? parseInt(parsed[1], 10) : 0
  const tier: "NEW" | "MAX" | "UPGRADE" = offer.isNew ? "NEW" : cur >= cap ? "MAX" : "UPGRADE"
  const tierChip =
    tier === "NEW"
      ? { label: "首次解锁", cls: "border-amber-300/30 bg-amber-400/15 text-amber-100/90" }
      : tier === "MAX"
        ? { label: "已满级", cls: "border-amber-300/30 bg-amber-400/15 text-amber-200/90" }
        : { label: "进阶强化", cls: "border-[#8CBEAA]/30 bg-[#8CBEAA]/12 text-[#CFE8DE]" }

  // 鼠标聚光边框（useMotionValue 非 useState，符合动效规范）
  const mx = useMotionValue(-240)
  const my = useMotionValue(-240)
  const spotlight = useMotionTemplate`radial-gradient(300px at ${mx}px ${my}px, rgba(255,255,255,0.12), rgba(255,255,255,0) 70%)`

  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, y: 28, scale: 0.94 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: 0.08 * index, type: "spring", stiffness: 320, damping: 26 }}
      onClick={onPick}
      onMouseMove={(e: React.MouseEvent<HTMLButtonElement>) => {
        const r = e.currentTarget.getBoundingClientRect()
        mx.set(e.clientX - r.left)
        my.set(e.clientY - r.top)
      }}
      onMouseLeave={() => {
        mx.set(-240)
        my.set(-240)
      }}
      className="group relative w-full max-w-[280px] overflow-hidden rounded-2xl border border-white/[0.14] bg-surface-2/75 text-left shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_24px_80px_rgba(0,0,0,0.55)] backdrop-blur-2xl transition hover:-translate-y-0.5 hover:border-white/25 hover:bg-surface-2/90 active:scale-[0.98] sm:max-w-none"
      style={{ WebkitBackdropFilter: "blur(28px) saturate(160%)" }}
    >
      <div className={`pointer-events-none absolute -right-10 -top-10 h-36 w-36 rounded-full bg-gradient-to-br ${meta.bar} opacity-30 blur-2xl`} />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/40 to-transparent opacity-40 transition group-hover:opacity-90" />
      <motion.div className="pointer-events-none absolute inset-0" style={{ background: spotlight }} />
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute inset-y-0 left-0 w-1/3 -skew-x-12 bg-gradient-to-r from-transparent via-white/[0.07] to-transparent opacity-0 group-hover:animate-[nebula-sheen_0.8s_ease-out_forwards] group-hover:opacity-100" />
      </div>

      <div className="relative p-4 sm:p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-2.5">
            <span className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/[0.06] ${meta.line}`}>
              <TrackGlyph id={offer.trackId} />
            </span>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-mono-data text-[9px] uppercase tracking-[0.2em] text-white/40">{meta.label}</span>
                <span className={`rounded-full border px-1.5 py-px text-[9px] font-semibold tracking-wide ${tierChip.cls}`}>{tierChip.label}</span>
              </div>
              <h3 className="mt-1 font-display text-[15px] font-semibold leading-tight tracking-tight text-white sm:text-base">
                {offer.title}
              </h3>
            </div>
          </div>
          <span className="shrink-0 rounded-md border border-white/12 bg-black/30 px-2 py-1 font-mono-data text-[10px] font-semibold tabular-nums text-white/70">
            {offer.badgeLabel}
          </span>
        </div>

        <p className="mt-3 min-h-[2.6rem] text-[12px] leading-relaxed text-white/55">{offer.desc}</p>

        <div className="mt-3 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Pips level={cur} max={cap} barClass={meta.bar} />
            <span className="font-mono-data text-[10px] tabular-nums text-white/40">{cur}/{cap}</span>
          </div>
          <span className={`inline-flex items-center rounded-full bg-gradient-to-r ${meta.bar} px-4 py-1.5 text-[12px] font-semibold text-gray-950 shadow-lg`}>
            选取
          </span>
        </div>
      </div>
    </motion.button>
  )
}

export function NebulaSurvivorGame() {
  useArcadeAccent("nebula-survivor")
  const { isMobile } = useMobileGameViewport()
  const containerRef = React.useRef<HTMLDivElement>(null)
  const engineRef = React.useRef<NebulaEngine | null>(null)
  const rafRef = React.useRef<number>(0)

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
  const [sfxOn, setSfxOn] = React.useState(() => nebulaSfx.volume > 0.001)

  const rulesOpenRef = React.useRef(rulesModalOpen)
  const rulesKindRef = React.useRef(rulesModalKind)

  // 弹层焦点陷阱 + Esc 已移交共享的 ArcadeEntry：briefing 不传 onRequestClose
  // → closeOnEsc=false（必须显式点「开始任务」）；pause / reference 传 onRequestClose 才可 Esc 关闭。
  // 与既有 Esc/P 语义保持一致。

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
    upgrades: { fire_salvo: 1, fire_rate: 1, ring_count: 0, ring_spin: 0, afterburner: 0 } as Record<UpgradeTrackId, number>,
    gameTime: 0,
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
      upgrades: { ...g.upgrades },
      gameTime: g.gameTime,
    })
  }, [])

  React.useLayoutEffect(() => {
    try {
      if (localStorage.getItem(NEBULA_STORAGE_SKIP_RULES) === "1") setRulesModalOpen(false)
    } catch {
      /* ignore */
    }
  }, [])

  // 首次手势恢复 AudioContext（autoplay 合规：手势前静默）
  React.useEffect(() => {
    const resume = () => nebulaSfx.ensure()
    window.addEventListener("pointerdown", resume, { once: true })
    window.addEventListener("keydown", resume, { once: true })
    return () => {
      window.removeEventListener("pointerdown", resume)
      window.removeEventListener("keydown", resume)
    }
  }, [])

  React.useLayoutEffect(() => {
    const container = containerRef.current
    if (!container) return
    const host = new NebulaPixiHost()
    const engine = host.engine
    engineRef.current = engine

    let disposed = false
    void host.mount(container).then(() => {
      if (disposed) {
        host.destroy()
        return
      }
      let uiAcc = 0
      let lastUi = performance.now()
      let lastPause = engine.pausedUpgrade
      let lastOver = engine.gameOver
      const loop = () => {
        const g = engineRef.current
        if (g) {
          let mx = keyRef.current.x + joyRef.current.x
          let my = keyRef.current.y + joyRef.current.y
          const m = Math.hypot(mx, my)
          if (m > 1) {
            mx /= m
            my /= m
          }
          g.moveX = mx
          g.moveY = my

          const now = performance.now()
          uiAcc += (now - lastUi) / 1000
          lastUi = now
          const changed = g.pausedUpgrade !== lastPause || g.gameOver !== lastOver
          lastPause = g.pausedUpgrade
          lastOver = g.gameOver
          if (uiAcc >= 0.1 || changed) {
            uiAcc = 0
            syncUi()
          }
        }
        rafRef.current = requestAnimationFrame(loop)
      }
      rafRef.current = requestAnimationFrame(loop)
      syncUi()
    })

    return () => {
      disposed = true
      cancelAnimationFrame(rafRef.current)
      host.destroy()
      engineRef.current = null
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
    (e: React.PointerEvent<HTMLDivElement>) => {
      const g = engineRef.current
      const c = containerRef.current
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
    syncUi()
  }, [syncUi])

  const blocked = rulesModalOpen || ui.pausedUpgrade || ui.gameOver

  return (
    <div
      className="relative flex h-dvh min-h-0 flex-col overflow-hidden bg-space-black text-white"
      style={arcadeAccentStyle("nebula-survivor")}
    >
      <HudTopBar
        layout="spread"
        className="z-10 shrink-0 border-b border-white/[0.07] bg-black/30 px-3 py-2 backdrop-blur-xl sm:px-5 sm:py-2.5"
        left={
          <div className="flex w-24 items-center sm:w-28">
            {isMobile ? null : <GameBackButton variant="header" label="大厅" />}
          </div>
        }
        center={<BrandMark slug="nebula-survivor" className="sm:[&_span]:text-[12px]" />}
        right={
          <div className="flex w-24 items-center justify-end gap-1.5 sm:w-28">
          {!isMobile ? (
            <>
              <button
                type="button"
                title={sfxOn ? "音效：开" : "音效：关"}
                aria-label={sfxOn ? "关闭音效" : "开启音效"}
                onClick={() => {
                  const next = !sfxOn
                  setSfxOn(next)
                  nebulaSfx.volume = next ? 0.6 : 0
                }}
                className="flex min-h-[32px] w-8 items-center justify-center rounded-full border border-white/12 bg-white/[0.06] text-white/80 backdrop-blur-md transition hover:bg-white/[0.11] active:scale-[0.97]"
              >
                {sfxOn ? <Volume2 className="h-3.5 w-3.5" /> : <VolumeX className="h-3.5 w-3.5" />}
              </button>
              <button
                type="button"
                title="暂停（战斗中按 P 亦可）"
                disabled={ui.gameOver || ui.pausedUpgrade || rulesModalOpen}
                onClick={() => {
                  setRulesModalKind("pause")
                  setRulesModalOpen(true)
                }}
                className="flex min-h-[32px] items-center justify-center rounded-full border border-white/12 bg-white/[0.06] px-3 text-[11px] font-medium text-white/80 backdrop-blur-md transition hover:bg-white/[0.11] active:scale-[0.97] disabled:pointer-events-none disabled:opacity-35"
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
                className="flex min-h-[32px] items-center justify-center rounded-full border border-white/12 bg-white/[0.06] px-3 text-[11px] font-medium text-white/80 backdrop-blur-md transition hover:bg-white/[0.11] active:scale-[0.97] disabled:pointer-events-none disabled:opacity-35"
              >
                规则
              </button>
            </>
          ) : null}
          </div>
        }
      />

      {isMobile && !rulesModalOpen && !ui.pausedUpgrade && !ui.gameOver ? (
        <StagePortal>
          <GameBackButton variant="floating" label="大厅" />
          <div
            className="fixed z-[70] flex flex-col gap-2"
            style={{
              top: "max(0.75rem, env(safe-area-inset-top, 0px))",
              right: "max(0.75rem, env(safe-area-inset-right, 0px))",
            }}
          >
            <button
              type="button"
              title="暂停（战斗中按 P 亦可）"
              disabled={ui.gameOver || ui.pausedUpgrade || rulesModalOpen}
              onClick={() => {
                setRulesModalKind("pause")
                setRulesModalOpen(true)
              }}
              className="flex min-h-[44px] min-w-[44px] items-center justify-center rounded-full border border-white/15 bg-black/45 px-3.5 text-[12px] font-medium text-white/85 backdrop-blur-md disabled:pointer-events-none disabled:opacity-35 active:scale-[0.97]"
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
              className="flex min-h-[44px] min-w-[44px] items-center justify-center rounded-full border border-white/15 bg-black/45 px-3.5 text-[12px] font-medium text-white/85 backdrop-blur-md disabled:pointer-events-none disabled:opacity-35 active:scale-[0.97]"
            >
              规则
            </button>
          </div>
        </StagePortal>
      ) : null}

      <div className="relative min-h-0 flex-1">
        <div className="pointer-events-none absolute left-3 top-2 z-10 w-[15rem] sm:left-5 sm:top-4 sm:w-64">
          <div className="relative flex flex-col gap-2.5 overflow-hidden rounded-xl border border-white/10 bg-surface-2/80 px-3.5 py-3 shadow-[0_16px_48px_-12px_rgba(0,0,0,0.7),inset_0_1px_0_rgba(255,255,255,0.06)] backdrop-blur-glass-md">
            <PanelCorners />
            <div className="flex items-baseline justify-between font-mono-data">
              <span className="text-[11px] font-semibold tracking-[0.14em] text-white/85">
                WAVE <span className="text-hud-accent-bright">{String(ui.worldTier).padStart(2, "0")}</span>
              </span>
              <span className="text-[10px] uppercase tracking-[0.18em] text-white/45">
                LV <span className="text-white/80">{ui.level}</span>
              </span>
            </div>
            <HudMeter
              label="HP"
              labelClassName="w-6 shrink-0 text-right text-[10px] font-semibold tracking-wider text-white/60"
              value={ui.hp}
              max={ui.maxHp}
              variant="hp"
              skew={false}
              barClassName="h-2"
              text={`${Math.round(ui.hp)}/${ui.maxHp}`}
              valueClassName="w-11 shrink-0 text-right text-[10px] tabular-nums text-white/55"
            />
            <HudMeter
              label="XP"
              labelClassName="w-6 shrink-0 text-right text-[10px] font-semibold tracking-wider text-hud-green/70"
              value={ui.xp}
              max={ui.xpToNext}
              variant="xp"
              text={`${Math.floor(ui.xp)}/${ui.xpToNext}`}
              valueClassName="w-11 shrink-0 text-right text-[10px] tabular-nums text-white/55"
            />
            <div className="flex items-center justify-between border-t border-white/[0.07] pt-2 font-mono-data text-[10px] tabular-nums">
              <HudStat label="击杀" className="text-white/45" value={ui.kills} valueClassName="text-white/85" />
              <span className="h-3 w-px bg-white/10" />
              <HudStat
                label="得分"
                className="text-white/45"
                value={ui.score}
                valueClassName="text-hud-accent-bright"
              />
              <span className="h-3 w-px bg-white/10" />
              <HudStat
                label="威胁"
                className="text-white/45"
                value={ui.worldTier >= 5 ? "高" : ui.worldTier >= 3 ? "中" : "低"}
                valueClassName="text-[#D98A72]"
              />
            </div>
            <div className="flex items-center justify-between border-t border-white/[0.07] pt-2">
              {(Object.keys(TRACK_META) as UpgradeTrackId[]).map((id) => {
                const lv = ui.upgrades[id]
                const meta = TRACK_META[id]
                const active = lv > 0
                return (
                  <div key={id} className="flex w-8 flex-col items-center gap-1" title={`${meta.label} Lv${lv}`}>
                    <TrackGlyph id={id} className={active ? meta.line : "text-white/22"} />
                    <span className={`font-mono-data text-[9px] leading-none tabular-nums ${active ? "text-white/70" : "text-white/20"}`}>
                      {active ? lv : "·"}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        <div
          ref={containerRef}
          className={`block h-full w-full touch-none ${blocked ? "pointer-events-none" : ""}`}
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

        <p className="pointer-events-none absolute bottom-[max(0.35rem,env(safe-area-inset-bottom))] right-2 z-10 max-w-[12rem] text-[9px] leading-snug text-white/50 sm:bottom-3 sm:right-5 sm:max-w-none sm:text-[10px]">
          WASD / 方向键 · 指针滑移 · 左下摇杆 · <span className="text-white/50">P 暂停</span>（暂停时见规则）
        </p>
      </div>

      {rulesModalOpen ? (
        <ArcadeEntry
          slug="nebula-survivor"
          titleId="nebula-rules-title"
          brandInline={false}
          title={<BrandMark slug="nebula-survivor" variant="title" />}
          titleClassName="mt-2 flex justify-center"
          subtitle={
            rulesModalKind === "briefing"
              ? "读完后点击「开始任务」进入战场"
              : rulesModalKind === "pause"
                ? "游戏已暂停 · 可复习下方规则，关闭后继续战斗（Esc / P 亦可关闭）"
                : "查阅完毕后点击下方按钮返回游戏"
          }
          subtitleClassName="mt-1 text-center text-[12px] text-white/50"
          eyebrow={
            <>
              <p className="text-center text-[10px] font-semibold uppercase tracking-[0.26em] text-white/50">Briefing</p>
              {rulesModalKind === "pause" ? (
                <div className="mt-2 flex justify-center">
                  <span className="rounded-full border border-amber-200/25 bg-amber-400/15 px-3 py-1 text-[11px] font-semibold tracking-wide text-amber-100/95">
                    已暂停
                  </span>
                </div>
              ) : null}
            </>
          }
          panelOverlay={<PanelCorners className="text-hud-accent/60" />}
          panelClassName="relative"
          overlayZClassName="z-40"
          overlayTint="bg-black/58"
          overlayPadding="sm:p-5"
          safeArea
          label={rulesModalKind === "briefing" ? "开始任务" : rulesModalKind === "pause" ? "继续游戏" : "返回游戏"}
          onConfirm={closeRulesPrimary}
          onRequestClose={rulesModalKind === "briefing" ? undefined : () => setRulesModalOpen(false)}
          confirmClassName="mt-4 w-full rounded-xl bg-gradient-to-r from-amber-400 via-amber-500 to-amber-600 py-3.5 text-[15px] font-semibold text-gray-950 shadow-[0_10px_32px_-8px_rgba(216,163,60,0.55)] transition hover:brightness-110 active:scale-[0.99]"
          skipRules={
            rulesModalKind === "briefing"
              ? {
                  checked: dontShowRulesAgain,
                  onChange: setDontShowRulesAgain,
                  label: "下次不再显示（本机记住）",
                  className: "mt-4 px-3 py-2.5 text-[12px] text-white/68",
                }
              : undefined
          }
          footer={
            <p className="mt-3 text-center font-display text-[10px] uppercase tracking-[0.3em] text-white/30">
              AsterNova · Arcade
            </p>
          }
        >
            <ul className="mt-5 space-y-3.5 text-[13px] leading-relaxed text-white/78">
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <NebulaIconMove />
                <div>
                  <div className="font-medium text-white/95">移动</div>
                  <div className="mt-0.5 text-[12px] text-white/52">
                    <span className="text-hud-accent-bright">WASD / 方向键</span>，指针在画面上可向鼠标方向滑移；手机用左下摇杆。
                  </div>
                </div>
              </li>
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <NebulaIconLaser />
                <div>
                  <div className="font-medium text-white/95">火力覆盖</div>
                  <div className="mt-0.5 text-[12px] text-white/52">
                    琥珀弹幕仅在<span className="text-hud-accent-bright">视野相近范围</span>内锁定最近敌人；可分别强化<span className="text-hud-accent-bright">齐射发数</span>与<span className="text-hud-accent-bright">射速</span>。
                  </div>
                </div>
              </li>
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <NebulaIconEye />
                <div>
                  <div className="font-medium text-white/95">敌人察觉</div>
                  <div className="mt-0.5 text-[12px] text-white/52">
                    屏外敌人会先<span className="text-[#8CBEAA]">短暂靠近再游荡</span>；一旦<span className="text-[#8CBEAA]">出现在视野内</span>或<span className="text-[#8CBEAA]">进入察觉范围</span>即持续追击。最小档有暖色外圈描边。
                  </div>
                </div>
              </li>
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <NebulaIconHeart />
                <div>
                  <div className="font-medium text-white/95">升级与急救</div>
                  <div className="mt-0.5 text-[12px] text-white/52">
                    五条强化（火力弹幕/射速、星环数量/转速、推进器）中<span className="text-[#8CBEAA]">随机三选一</span>，每级可<span className="text-[#8CBEAA]">免费刷新一次</span>。击杀<span className="text-[#CFE8DE]">极低概率</span>掉急救包。
                  </div>
                </div>
              </li>
            </ul>
        </ArcadeEntry>
      ) : null}

      <StagePortal>
      <AnimatePresence>
        {ui.pausedUpgrade && ui.choices.length > 0 ? (
          <motion.div
            className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 p-3 backdrop-blur-xl sm:p-6"
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
              className="relative max-h-[92dvh] w-full max-w-[920px] overflow-y-auto rounded-[1.75rem] border-[0.5px] border-white/[0.12] bg-white/[0.06] p-4 shadow-[0_32px_100px_rgba(0,0,0,0.65),inset_0_1px_0_rgba(255,255,255,0.06)] sm:rounded-[2rem] sm:p-8"
              style={{ WebkitBackdropFilter: "blur(32px) saturate(170%)" }}
            >
              <PanelCorners className="text-hud-accent/60" />
              <p className="text-center text-[10px] font-semibold uppercase tracking-[0.28em] text-white/50">Time Stop</p>
              <h2 className="mt-2 text-center text-xl font-semibold tracking-tight text-white sm:text-2xl">选择一项升级</h2>
              <p className="mx-auto mt-1 max-w-md text-center text-[13px] text-white/50">
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
      </StagePortal>

      <StagePortal>
      <AnimatePresence>
        {ui.gameOver ? (
          <ArcadeResult
            slug="nebula-survivor"
            score={ui.score}
            title="SIGNAL LOST"
            subtitle="信号丢失 · 暗物质潮淹没宇航服护盾"
            extraStats={[
              { label: "击杀", value: ui.kills },
              { label: "存活", value: formatTime(ui.gameTime) },
              { label: "等级", value: ui.level },
              { label: "波次", value: ui.worldTier },
            ]}
            actionLabel="再闯星云"
            onAction={restart}
          />
        ) : null}
      </AnimatePresence>
      </StagePortal>
      <LoopingBgmControl src="/audio/games/nebula-survivor/Untitled.mp3" storageKey="bgm-volume:nebula-survivor" hidden={rulesModalOpen || ui.pausedUpgrade || ui.gameOver} />
    </div>
  )
}
