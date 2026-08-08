"use client"

/**
 * AsterNova Merge — Matter.js + Apple 风 UI + Framer Motion
 */

import * as React from "react"
import { useRouter } from "next/navigation"
import { Bodies, Body, Composite, Engine, Events, Render, Runner, World } from "matter-js"
import { AnimatePresence, motion } from "framer-motion"
import { LoopingBgmControl } from "@/src/components/audio/LoopingBgmControl"

const MERGE_STORAGE_SKIP_RULES = "merge-skip-rules"

const WORLD_W = 400
const WORLD_H = 640
/** 舞台在 CSS 中的最大宽度；实际宽度还受视口高度限制以保持整屏可见 */
const STAGE_MAX_CSS_W = 560
/** 顶部预览条高度占舞台比例（与 Tailwind h-[22%] 一致） */
const PREVIEW_STRIP_H = 0.22
const WALL_T = 24
const FLOOR_H = 38
const RESTITUTION = 0.32
const DANGER_Y = 96
const FAIL_HOLD_MS = 3000
const DROP_COOLDOWN_MS = 420

export type StarTier = {
  level: number
  radius: number
  name: string
  /** 高光 → 边缘：粉珊瑚 → 琥珀 → 青绿 → 天蓝 → 月灰（避免刺眼电紫） */
  highlight: string
  core: string
  mid: string
  rim: string
  edge: string
  glow: string
}

/** 10 档：更大半径 + 每档独立渐变节点 */
export const STAR_TIERS: StarTier[] = [
  { level: 1, radius: 20, name: "星尘", highlight: "#fff8fb", core: "#ffeef6", mid: "#ffd0e5", rim: "#fb9cc8", edge: "rgba(251,113,133,0.9)", glow: "rgba(253,164,175,0.48)" },
  { level: 2, radius: 24, name: "微光", highlight: "#fff5f7", core: "#ffe4e9", mid: "#fda4af", rim: "#fb7185", edge: "rgba(251,113,133,0.88)", glow: "rgba(251,113,133,0.44)" },
  { level: 3, radius: 28, name: "流萤", highlight: "#fff5f3", core: "#ffe7dc", mid: "#fdbcb4", rim: "#fb7185", edge: "rgba(251,113,133,0.86)", glow: "rgba(253,186,168,0.42)" },
  { level: 4, radius: 32, name: "晨星", highlight: "#fff8f3", core: "#ffedd5", mid: "#fdba74", rim: "#fb923c", edge: "rgba(249,115,22,0.85)", glow: "rgba(251,146,60,0.4)" },
  { level: 5, radius: 36, name: "辉星", highlight: "#fffbeb", core: "#fef3c7", mid: "#fcd34d", rim: "#f59e0b", edge: "rgba(217,119,6,0.88)", glow: "rgba(245,158,11,0.42)" },
  { level: 6, radius: 40, name: "琥光", highlight: "#fffbeb", core: "#fef9c3", mid: "#fde047", rim: "#ca8a04", edge: "rgba(202,138,4,0.9)", glow: "rgba(234,179,8,0.45)" },
  { level: 7, radius: 45, name: "潮青", highlight: "#f0fdfa", core: "#ccfbf1", mid: "#5eead4", rim: "#0d9488", edge: "rgba(13,148,136,0.88)", glow: "rgba(45,212,191,0.44)" },
  { level: 8, radius: 50, name: "天幕", highlight: "#f0f9ff", core: "#e0f2fe", mid: "#7dd3fc", rim: "#0284c7", edge: "rgba(2,132,199,0.9)", glow: "rgba(56,189,248,0.42)" },
  { level: 9, radius: 56, name: "瀚波", highlight: "#eff6ff", core: "#dbeafe", mid: "#60a5fa", rim: "#1d4ed8", edge: "rgba(29,78,216,0.9)", glow: "rgba(59,130,246,0.44)" },
  { level: 10, radius: 62, name: "星冕", highlight: "#fefdfb", core: "#f8fafc", mid: "#e2e8f0", rim: "#94a3b8", edge: "rgba(71,85,105,0.92)", glow: "rgba(148,163,184,0.5)" },
]

type StarBody = Body & { starLevel?: number }

function tierByLevel(l: number): StarTier {
  return STAR_TIERS[Math.min(10, Math.max(1, l)) - 1]
}

function rollBaseDropLevel(): number {
  return Math.random() < 0.5 ? 1 : Math.random() < 0.65 ? 2 : 3
}

/**
 * 下一颗球：默认仍为 Lv1–3；分数越高，越有小幅概率直接掉落 Lv4–7「大号赠送球」。
 * 概率有硬顶，避免后期全是巨球破坏节奏。
 */
function randomNextDropLevel(score: number): number {
  const bonusChance = score < 320 ? 0 : Math.min(0.125, 0.012 + score / 6500)
  if (Math.random() >= bonusChance) return rollBaseDropLevel()
  const r = Math.random()
  if (r < 0.5) return 4
  if (r < 0.76) return 5
  if (r < 0.92) return 6
  return 7
}

function tierOrbCssBackground(t: StarTier): string {
  return `radial-gradient(circle at 32% 26%, ${t.highlight} 0%, ${t.core} 28%, ${t.mid} 55%, ${t.rim} 78%, ${t.edge} 100%)`
}

type Ripple = { id: string; x: number; y: number; r: number }

function NextDropPanel({ tier }: { tier: StarTier }) {
  return (
    <div
      className="flex w-full flex-col items-center justify-center gap-2.5 rounded-[18px] border-[0.5px] border-white/[0.18] bg-white/[0.06] px-3 py-3.5 shadow-[0_1px_0_rgba(255,255,255,0.05)_inset,0_12px_40px_rgba(0,0,0,0.35)] backdrop-blur-[18px] sm:rounded-[20px] sm:py-4 md:min-h-[200px] md:w-[118px]"
      style={{ WebkitBackdropFilter: "blur(18px)" }}
    >
      <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-white/40">下一颗</p>
      <div
        className="relative flex h-[88px] w-[88px] items-center justify-center rounded-2xl border-[0.5px] border-white/15 bg-black/25"
        style={{
            boxShadow: `0 0 0 1px rgba(255,255,255,0.04) inset, 0 12px 36px ${tier.glow}`,
        }}
      >
        <div
          className="rounded-full"
          style={{
            width: Math.min(72, tier.radius * 2.1),
            height: Math.min(72, tier.radius * 2.1),
            background: tierOrbCssBackground(tier),
            boxShadow: `0 0 20px ${tier.glow}, 0 0 36px rgba(45,212,191,0.1), inset 0 0 14px rgba(255,255,255,0.35)`,
            border: "0.5px solid rgba(255,255,255,0.22)",
          }}
        />
      </div>
      <div className="text-center">
        <p className="text-[11px] font-semibold tabular-nums text-white/45">Lv.{tier.level}</p>
        <p className="mt-0.5 text-[13px] font-medium tracking-tight text-white/90">{tier.name}</p>
      </div>
    </div>
  )
}

function MergeIconDrop({ className, iconClass }: { className?: string; iconClass?: string }) {
  return (
    <span
      className={`flex shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-300/40 to-amber-300/30 ${iconClass ?? "h-11 w-11"} ${className ?? ""}`}
      aria-hidden
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-white">
        <path
          d="M12 5v8M12 13l-3-3m3 3l3-3"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity={0.85}
        />
        <circle cx="12" cy="18" r="3.5" stroke="currentColor" strokeWidth="1.5" />
      </svg>
    </span>
  )
}

function MergeIconFuse({ className, iconClass }: { className?: string; iconClass?: string }) {
  return (
    <span
      className={`flex shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-200/38 to-teal-400/28 ${iconClass ?? "h-11 w-11"} ${className ?? ""}`}
      aria-hidden
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-white">
        <circle cx="8.5" cy="12" r="3.25" stroke="currentColor" strokeWidth="1.45" />
        <circle cx="15.5" cy="12" r="3.25" stroke="currentColor" strokeWidth="1.45" />
        <path d="M11.5 12h1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <path
          d="M12 8v2M12 14v2"
          stroke="currentColor"
          strokeWidth="1.2"
          strokeLinecap="round"
          opacity={0.6}
        />
      </svg>
    </span>
  )
}

function MergeIconDanger({ className, iconClass }: { className?: string; iconClass?: string }) {
  return (
    <span
      className={`flex shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-400/32 to-orange-400/25 ${iconClass ?? "h-11 w-11"} ${className ?? ""}`}
      aria-hidden
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-white">
        <path
          d="M4 9h16M4 15h16"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeDasharray="3 3"
          opacity={0.9}
        />
        <path d="M6 6l12 12" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" opacity={0.35} />
      </svg>
    </span>
  )
}

function MergeIconNext({ className, iconClass }: { className?: string; iconClass?: string }) {
  return (
    <span
      className={`flex shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-300/32 to-sky-500/28 ${iconClass ?? "h-11 w-11"} ${className ?? ""}`}
      aria-hidden
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-white">
        <circle cx="9" cy="10" r="3" stroke="currentColor" strokeWidth="1.4" />
        <circle cx="15" cy="14" r="2.25" stroke="currentColor" strokeWidth="1.35" opacity={0.75} />
        <path
          d="M12 6v2M16 8l1.5-1.5M16 8l-1.5-1.5"
          stroke="currentColor"
          strokeWidth="1.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity={0.7}
        />
      </svg>
    </span>
  )
}

export function MergeGame() {
  const router = useRouter()
  const shellRef = React.useRef<HTMLDivElement | null>(null)
  const stageRef = React.useRef<HTMLDivElement | null>(null)
  const engineRef = React.useRef<Engine | null>(null)
  const renderRef = React.useRef<Render | null>(null)
  const runnerRef = React.useRef<Runner | null>(null)

  const [mouseNorm, setMouseNorm] = React.useState({ x: 0.5, y: 0.5 })
  const [score, setScore] = React.useState(0)
  const scoreRef = React.useRef(0)
  const [highScore, setHighScore] = React.useState(0)
  const [playing, setPlaying] = React.useState(true)
  const [ripples, setRipples] = React.useState<Ripple[]>([])
  const [ghostX, setGhostX] = React.useState(WORLD_W / 2)
  /** SSR/首帧固定为 1，避免与 random 不一致导致 hydration 报错 */
  const [nextLevel, setNextLevel] = React.useState(1)
  const [rulesModalOpen, setRulesModalOpen] = React.useState(true)
  const [dontShowRulesAgain, setDontShowRulesAgain] = React.useState(false)
  const nextLevelRef = React.useRef(1)
  const ghostXRef = React.useRef(WORLD_W / 2)
  const playingRef = React.useRef(true)
  const lastDropAtRef = React.useRef(0)
  const dangerAccumRef = React.useRef(0)
  const mergeBusyRef = React.useRef(false)

  React.useLayoutEffect(() => {
    const n = randomNextDropLevel(0)
    nextLevelRef.current = n
    setNextLevel(n)
  }, [])

  React.useEffect(() => {
    try {
      if (localStorage.getItem(MERGE_STORAGE_SKIP_RULES) === "1") setRulesModalOpen(false)
    } catch {
      /* ignore */
    }
  }, [])

  const confirmMergeRules = React.useCallback(() => {
    try {
      if (dontShowRulesAgain) localStorage.setItem(MERGE_STORAGE_SKIP_RULES, "1")
    } catch {
      /* ignore */
    }
    setRulesModalOpen(false)
  }, [dontShowRulesAgain])

  React.useEffect(() => {
    scoreRef.current = score
  }, [score])

  React.useEffect(() => {
    nextLevelRef.current = nextLevel
  }, [nextLevel])
  React.useEffect(() => {
    ghostXRef.current = ghostX
  }, [ghostX])
  React.useEffect(() => {
    playingRef.current = playing
  }, [playing])

  const pushRipple = React.useCallback((wx: number, wy: number, radiusHint: number) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
    setRipples((prev) => [...prev, { id, x: wx, y: wy, r: radiusHint }])
    window.setTimeout(() => {
      setRipples((prev) => prev.filter((r) => r.id !== id))
    }, 700)
  }, [])

  const dropBall = React.useCallback(
    (clientX: number) => {
    const render = renderRef.current
    const engine = engineRef.current
    if (!render || !engine || !playingRef.current || rulesModalOpen) return
    const now = performance.now()
    if (now - lastDropAtRef.current < DROP_COOLDOWN_MS) return
    lastDropAtRef.current = now

    const rect = render.canvas.getBoundingClientRect()
    const sx = WORLD_W / rect.width
    const x = (clientX - rect.left) * sx
    const level = nextLevelRef.current
    const t = tierByLevel(level)
    const clamped = Math.max(t.radius + WALL_T + 4, Math.min(WORLD_W - t.radius - WALL_T - 4, x))
    const y = DANGER_Y + t.radius + 38

    const body = Bodies.circle(clamped, y, t.radius, {
      label: "merge-star",
      restitution: RESTITUTION,
      friction: 0.08,
      frictionAir: 0.008,
      density: 0.00175,
      render: { visible: false },
    }) as StarBody
    body.starLevel = level
    World.add(engine.world, body)

    const nl = randomNextDropLevel(scoreRef.current)
    nextLevelRef.current = nl
    setNextLevel(nl)
  },
    [rulesModalOpen],
  )

  const dropAtCurrentAim = React.useCallback(() => {
    const render = renderRef.current
    if (!render) return
    const rect = render.canvas.getBoundingClientRect()
    const clientX = rect.left + (ghostXRef.current / WORLD_W) * rect.width
    dropBall(clientX)
  }, [dropBall])

  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.code === "KeyE" || e.code === "Space") {
        e.preventDefault()
        dropAtCurrentAim()
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [dropAtCurrentAim])

  React.useEffect(() => {
    const el = stageRef.current
    if (!el) return

    const engine = Engine.create({
      gravity: { x: 0, y: 1, scale: 0.001 },
    })
    engineRef.current = engine

    const render = Render.create({
      element: el,
      engine,
      options: {
        width: WORLD_W,
        height: WORLD_H,
        wireframes: false,
        background: "transparent",
        pixelRatio: Math.min(2, typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1),
      },
    })
    renderRef.current = render
    const canvas = render.canvas
    canvas.style.width = "100%"
    canvas.style.height = "100%"
    canvas.style.display = "block"
    canvas.style.borderRadius = "22px"

    const wallOpts = {
      isStatic: true,
      render: { visible: false },
      friction: 0.42,
      restitution: 0.2,
    }
    const walls = [
      Bodies.rectangle(WORLD_W / 2, WORLD_H + FLOOR_H / 2, WORLD_W + 80, FLOOR_H, wallOpts),
      Bodies.rectangle(-WALL_T / 2, WORLD_H / 2, WALL_T, WORLD_H + 200, wallOpts),
      Bodies.rectangle(WORLD_W + WALL_T / 2, WORLD_H / 2, WALL_T, WORLD_H + 200, wallOpts),
    ]
    World.add(engine.world, walls)

    const runner = Runner.create()
    runnerRef.current = runner

    const getStarBodies = () =>
      Composite.allBodies(engine.world).filter((b) => b.label === "merge-star") as StarBody[]

    const spawnStar = (level: number, x: number, y: number) => {
      const t = tierByLevel(level)
      const body = Bodies.circle(x, y, t.radius, {
        label: "merge-star",
        restitution: RESTITUTION,
        friction: 0.08,
        frictionAir: 0.008,
        density: 0.00175,
        render: { visible: false },
      }) as StarBody
      body.starLevel = level
      World.add(engine.world, body)
      return body
    }

    Events.on(engine, "collisionStart", (event) => {
      if (!playingRef.current || mergeBusyRef.current) return
      mergeBusyRef.current = true
      try {
        const done = new Set<number>()
        for (const pair of event.pairs) {
          const a = pair.bodyA as StarBody
          const b = pair.bodyB as StarBody
          if (a.label !== "merge-star" || b.label !== "merge-star") continue
          const la = a.starLevel ?? 1
          const lb = b.starLevel ?? 1
          if (la !== lb || la >= 10) continue
          if (done.has(a.id) || done.has(b.id)) continue

          const mx = (a.position.x + b.position.x) / 2
          const my = Math.min(a.position.y, b.position.y) - 2
          World.remove(engine.world, [a, b])
          done.add(a.id)
          done.add(b.id)

          const nl = la + 1
          const nt = tierByLevel(nl)
          const nb = spawnStar(nl, mx, my)
          Body.setVelocity(nb, { x: (a.velocity.x + b.velocity.x) * 0.35, y: (a.velocity.y + b.velocity.y) * 0.35 - 0.5 })
          Body.setAngularVelocity(nb, (a.angularVelocity + b.angularVelocity) * 0.25)

          setScore((s) => {
            const add = nl * nl * 10
            const v = s + add
            setHighScore((h) => Math.max(h, v))
            return v
          })
          pushRipple(mx, my, nt.radius)
        }
      } finally {
        requestAnimationFrame(() => {
          mergeBusyRef.current = false
        })
      }
    })

    Events.on(engine, "afterUpdate", () => {
      if (!playingRef.current) return
      let over = false
      for (const b of getStarBodies()) {
        const t = tierByLevel(b.starLevel ?? 1)
        const top = b.position.y - t.radius
        if (top < DANGER_Y) {
          over = true
          break
        }
      }
      const dt = typeof engine.timing.lastDelta === "number" ? engine.timing.lastDelta : 1000 / 60
      if (over) dangerAccumRef.current += dt
      else dangerAccumRef.current = 0
      if (dangerAccumRef.current >= FAIL_HOLD_MS) {
        playingRef.current = false
        setPlaying(false)
        setRulesModalOpen(false)
      }
    })

    Events.on(render, "afterRender", () => {
      const ctx = render.context
      ctx.save()
      ctx.strokeStyle = "rgba(248, 113, 113, 0.55)"
      ctx.lineWidth = 1.5
      ctx.setLineDash([6, 6])
      ctx.beginPath()
      ctx.moveTo(12, DANGER_Y)
      ctx.lineTo(WORLD_W - 12, DANGER_Y)
      ctx.stroke()
      ctx.setLineDash([])
      ctx.fillStyle = "rgba(248, 113, 113, 0.1)"
      ctx.fillRect(0, 0, WORLD_W, DANGER_Y)
      ctx.restore()

      for (const b of getStarBodies()) {
        const lv = b.starLevel ?? 1
        const t = tierByLevel(lv)
        const { x, y } = b.position
        const r = t.radius
        const g = ctx.createRadialGradient(x - r * 0.28, y - r * 0.3, r * 0.06, x, y, r * 1.18)
        g.addColorStop(0, t.highlight)
        g.addColorStop(0.22, t.core)
        g.addColorStop(0.48, t.mid)
        g.addColorStop(0.76, t.rim)
        g.addColorStop(1, t.edge)
        ctx.save()
        ctx.beginPath()
        ctx.arc(x, y, r, 0, Math.PI * 2)
        ctx.fillStyle = g
        ctx.shadowColor = t.glow
        ctx.shadowBlur = 18 + lv * 0.6
        ctx.fill()
        ctx.lineWidth = 1.1
        ctx.strokeStyle = "rgba(255,255,255,0.26)"
        ctx.stroke()
        ctx.restore()
      }
    })

    Render.run(render)
    Runner.run(runner, engine)

    return () => {
      Render.stop(render)
      Runner.stop(runner)
      Composite.clear(engine.world, false)
      Engine.clear(engine)
      if (canvas.parentNode) canvas.parentNode.removeChild(canvas)
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(render as any).textures = {}
    }
  }, [pushRipple])

  const onStagePointer = (e: React.PointerEvent) => {
    const render = renderRef.current
    if (!render) return
    const rect = render.canvas.getBoundingClientRect()
    const sx = WORLD_W / rect.width
    const x = (e.clientX - rect.left) * sx
    setGhostX(x)
  }

  const restart = () => {
    const engine = engineRef.current
    if (!engine) return
    const stars = Composite.allBodies(engine.world).filter((b) => b.label === "merge-star")
    World.remove(engine.world, stars)
    dangerAccumRef.current = 0
    playingRef.current = true
    setPlaying(true)
    setScore(0)
    scoreRef.current = 0
    const nl = randomNextDropLevel(0)
    nextLevelRef.current = nl
    setNextLevel(nl)
  }

  const previewTier = tierByLevel(nextLevel)

  const stageShellStyle = React.useMemo(
    () =>
      ({
        aspectRatio: `${WORLD_W} / ${WORLD_H}`,
        width: `min(100%, ${STAGE_MAX_CSS_W}px, calc((100dvh - 15.5rem) * ${WORLD_W} / ${WORLD_H}))`,
        maxWidth: "100%",
      }) satisfies React.CSSProperties,
    [],
  )

  return (
    <div
      ref={shellRef}
      className="relative flex h-full min-h-0 min-h-full flex-col overflow-hidden text-white"
      style={{
        backgroundColor: "#121212",
        fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif',
      }}
      onMouseMove={(e) => {
        if (!shellRef.current) return
        const r = shellRef.current.getBoundingClientRect()
        setMouseNorm({
          x: (e.clientX - r.left) / r.width,
          y: (e.clientY - r.top) / r.height,
        })
      }}
    >
      <div
        className="pointer-events-none fixed inset-0 z-0 transition-opacity duration-500"
        style={{
          background: `radial-gradient(42rem 42rem at ${mouseNorm.x * 100}% ${mouseNorm.y * 100}%, rgba(251,146,60,0.08), transparent 55%),
            radial-gradient(36rem 36rem at ${mouseNorm.x * 100 + 8}% ${mouseNorm.y * 100 - 5}%, rgba(45,212,191,0.07), transparent 50%)`,
        }}
      />

      <button
        type="button"
        onClick={() => setRulesModalOpen(true)}
        className="absolute z-30 rounded-full border-[0.5px] border-white/18 bg-white/[0.07] px-3 py-1.5 text-[11px] font-medium text-white/80 shadow-[0_8px_28px_rgba(0,0,0,0.35)] backdrop-blur-md transition hover:bg-white/[0.11] active:scale-[0.98] min-[400px]:px-3.5 min-[400px]:text-[12px] sm:right-6 sm:top-6"
        style={{
          WebkitBackdropFilter: "blur(14px)",
          top: "max(0.75rem, env(safe-area-inset-top, 0px))",
          right: "max(0.75rem, env(safe-area-inset-right, 0px))",
        }}
      >
        规则
      </button>

      <div className="relative z-10 mx-auto flex min-h-0 w-full max-w-[min(100%,42rem)] flex-1 flex-col gap-3 overflow-y-auto overscroll-y-contain px-[max(0.75rem,env(safe-area-inset-left))] pb-[max(0.75rem,env(safe-area-inset-bottom))] pr-[max(0.75rem,env(safe-area-inset-right))] pt-[max(0.35rem,env(safe-area-inset-top))] min-[400px]:gap-4 min-[400px]:px-4 min-[400px]:pb-6 min-[400px]:pt-4 sm:gap-4 sm:pb-6 sm:pt-4 lg:overflow-hidden">
        <motion.header
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-col items-center gap-0.5 text-center min-[400px]:gap-1"
        >
          <p className="text-[10px] font-medium uppercase tracking-[0.26em] text-white/35 min-[400px]:text-[11px] min-[400px]:tracking-[0.28em]">
            AsterNova
          </p>
          <h1 className="text-[clamp(1.25rem,4.5vw,1.65rem)] font-semibold tracking-tight text-white/95">Merge</h1>
          <p className="max-w-md px-1 text-center text-[12px] font-normal leading-snug text-white/45 sm:text-[13px] sm:leading-relaxed">
            <span className="sm:hidden">点击 / E / 空格下落</span>
            <span className="hidden sm:inline">
              同级相撞合成升级 · 越红线持续 3 秒结束 · 点击 / E 或空格下落
            </span>
          </p>
        </motion.header>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.08, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="relative mx-auto w-full"
        >
          <div
            className="relative overflow-hidden rounded-[22px] border-[0.5px] border-white/[0.22] bg-white/[0.04] p-2.5 shadow-[0_1px_0_rgba(255,255,255,0.06)_inset,0_24px_80px_rgba(0,0,0,0.45),0_0_0_1px_rgba(255,255,255,0.03),0_40px_100px_rgba(45,212,191,0.07)] backdrop-blur-[22px] backdrop-saturate-150 sm:rounded-[28px] sm:p-3"
            style={{ WebkitBackdropFilter: "blur(22px) saturate(150%)" }}
          >
            <div className="mb-2 flex flex-wrap items-center justify-end gap-x-2 gap-y-0.5 px-0.5 text-[11px] font-medium tabular-nums text-white/60 sm:mb-3 sm:text-[12px]">
              <span>
                {score} <span className="text-white/35">/</span> 最高 {highScore}
              </span>
            </div>

            <div className="flex flex-col gap-3 md:flex-row md:items-stretch md:gap-4">
              <div className="flex min-w-0 flex-1 justify-center">
                <div
                  ref={stageRef}
                  className={`relative cursor-crosshair touch-none overflow-hidden rounded-[18px] bg-black/[0.38] active:cursor-pointer sm:rounded-[22px] ${rulesModalOpen ? "pointer-events-none" : ""}`}
                  style={stageShellStyle}
                  onPointerMove={onStagePointer}
                  onPointerDown={(e) => {
                    onStagePointer(e)
                    dropBall(e.clientX)
                  }}
                >
                  <div className="pointer-events-none absolute inset-0 z-10 overflow-hidden rounded-[18px] sm:rounded-[22px]">
                    <AnimatePresence>
                      {ripples.map((rp) => (
                        <motion.div
                          key={rp.id}
                          className="pointer-events-none absolute rounded-full border border-amber-200/30 bg-gradient-to-br from-rose-300/22 to-teal-500/16"
                          style={{
                            left: `${((rp.x - rp.r) / WORLD_W) * 100}%`,
                            top: `${((rp.y - rp.r) / WORLD_H) * 100}%`,
                            width: `${((rp.r * 2) / WORLD_W) * 100}%`,
                            height: `${((rp.r * 2) / WORLD_H) * 100}%`,
                            boxShadow:
                              "0 0 28px rgba(251,146,60,0.28), 0 0 52px rgba(45,212,191,0.16), inset 0 0 22px rgba(255,255,255,0.1)",
                          }}
                          initial={{ scale: 0.2, opacity: 0.85 }}
                          animate={{ scale: 3.2, opacity: 0 }}
                          exit={{ opacity: 0 }}
                          transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
                        />
                      ))}
                    </AnimatePresence>
                  </div>

                  {playing ? (
                    <div
                      className="pointer-events-none absolute left-0 right-0 top-0 z-[5] h-[22%] rounded-t-[18px] sm:rounded-t-[22px]"
                      style={{
                        background: "linear-gradient(180deg, rgba(251,191,36,0.06), transparent)",
                      }}
                    >
                      <div
                        className="absolute top-[42%]"
                        style={{
                          left: `${((ghostX - previewTier.radius) / WORLD_W) * 100}%`,
                          width: `${((previewTier.radius * 2) / WORLD_W) * 100}%`,
                          height: `${((previewTier.radius * 2) / (PREVIEW_STRIP_H * WORLD_H)) * 100}%`,
                          borderRadius: "50%",
                          transform: "translateY(-50%)",
                          background: tierOrbCssBackground(previewTier),
                          boxShadow: `0 0 18px ${previewTier.glow}, 0 0 32px rgba(45,212,191,0.14), inset 0 0 14px rgba(255,255,255,0.32)`,
                          opacity: 0.92,
                          border: "0.5px solid rgba(255,255,255,0.24)",
                        }}
                      />
                    </div>
                  ) : null}
                </div>
              </div>

              <div className="flex justify-center md:w-[124px] md:shrink-0 md:justify-stretch">
                <NextDropPanel tier={previewTier} />
              </div>
            </div>

            <p className="mt-2 px-1 text-center text-[10px] font-normal leading-relaxed text-white/38 sm:mt-3 sm:text-[11px]">
              <span className="sm:hidden">移动准星 · 点按下落 · 同级合成</span>
              <span className="hidden sm:inline">
                在上方移动准星 · 点击画面、按 E 或空格在准星处下落 · 同级两球合成更高一级
              </span>
            </p>
          </div>
        </motion.div>

        <div className="flex flex-wrap items-center justify-center gap-2.5 pb-1 sm:gap-3 sm:pb-0">
          <button
            type="button"
            onClick={() => router.push("/lobby")}
            className="min-h-[44px] min-w-[44px] rounded-full border-[0.5px] border-white/15 bg-white/[0.06] px-4 py-2.5 text-[12px] font-medium text-white/85 shadow-[0_8px_32px_rgba(0,0,0,0.35)] backdrop-blur-md transition hover:bg-white/[0.1] active:scale-[0.98] sm:min-h-0 sm:px-5 sm:text-[13px]"
          >
            返回大厅
          </button>
          <button
            type="button"
            onClick={restart}
            className="min-h-[44px] min-w-[44px] rounded-full border-[0.5px] border-white/20 bg-gradient-to-r from-rose-400/90 via-amber-400/88 to-teal-500/88 px-5 py-2.5 text-[12px] font-semibold text-gray-950 shadow-[0_12px_40px_rgba(45,212,191,0.22),0_0_0_1px_rgba(255,255,255,0.15)_inset] transition hover:brightness-105 active:scale-[0.98] sm:min-h-0 sm:px-6 sm:text-[13px]"
          >
            再来一局
          </button>
        </div>
      </div>

      {rulesModalOpen ? (
        <div
          className="fixed inset-0 z-[55] flex items-end justify-center bg-black/55 backdrop-blur-md sm:items-center sm:p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="merge-rules-title"
          style={{
            paddingLeft: "max(0.75rem, env(safe-area-inset-left, 0px))",
            paddingRight: "max(0.75rem, env(safe-area-inset-right, 0px))",
            paddingBottom: "max(0.75rem, env(safe-area-inset-bottom, 0px))",
            paddingTop: "max(0.5rem, env(safe-area-inset-top, 0px))",
          }}
        >
          <div
            className="max-h-[min(88dvh,calc(100dvh-env(safe-area-inset-top)-env(safe-area-inset-bottom)-1.5rem))] w-full max-w-[420px] overflow-y-auto overscroll-contain rounded-t-[1.75rem] border border-white/[0.12] border-b-0 bg-white/[0.07] p-4 shadow-[0_24px_80px_rgba(0,0,0,0.55)] backdrop-blur-2xl sm:rounded-[2rem] sm:border-b sm:p-6"
            style={{ WebkitBackdropFilter: "blur(24px)" }}
          >
            <h2
              id="merge-rules-title"
              className="text-center text-xl font-semibold tracking-tight text-white"
              style={{ fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif" }}
            >
              怎么玩
            </h2>
            <p className="mt-1 text-center text-[13px] text-white/45">AsterNova · Merge · 星球合成</p>

            <ul className="mt-5 space-y-4 text-[14px] leading-relaxed text-white/80">
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <MergeIconDrop />
                <div>
                  <div className="font-medium text-white/95">下落</div>
                  <div className="mt-0.5 text-[13px] text-white/55">
                    在画面上移动准星；<span className="text-rose-200/90">点击</span>、按{" "}
                    <span className="text-amber-200/90">E</span> 或 <span className="text-amber-200/90">空格</span>{" "}
                    在准星位置释放当前球。
                  </div>
                </div>
              </li>
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <MergeIconFuse />
                <div>
                  <div className="font-medium text-white/95">合成</div>
                  <div className="mt-0.5 text-[13px] text-white/55">
                    两颗<span className="text-teal-200/90">相同等级</span>的球相撞会合成更高一级，并获得分数。
                  </div>
                </div>
              </li>
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <MergeIconDanger />
                <div>
                  <div className="font-medium text-white/95">警戒线</div>
                  <div className="mt-0.5 text-[13px] text-white/55">
                    堆叠超过顶部<span className="text-rose-200/85">红色虚线</span>并持续约 3 秒，本局结束。
                  </div>
                </div>
              </li>
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <MergeIconNext />
                <div>
                  <div className="font-medium text-white/95">下一颗</div>
                  <div className="mt-0.5 text-[13px] text-white/55">
                    右侧卡片预览下一颗球的等级与配色；共 10 档，从星尘到星冕。
                    <span className="mt-1 block text-[12px] text-white/45">
                      得分较高时，有小概率直接掉落 Lv4–7 大号赠送球。
                    </span>
                  </div>
                </div>
              </li>
            </ul>

            <label className="mt-5 flex cursor-pointer items-center gap-3 rounded-2xl border border-white/[0.08] bg-white/[0.04] px-4 py-3 text-[13px] text-white/70 transition hover:bg-white/[0.06]">
              <input
                type="checkbox"
                checked={dontShowRulesAgain}
                onChange={(e) => setDontShowRulesAgain(e.target.checked)}
                className="h-4 w-4 rounded-md border-white/30 bg-white/10 text-teal-500 focus:ring-teal-400/50"
              />
              下次不再显示规则（本机记住）
            </label>

            <button
              type="button"
              onClick={confirmMergeRules}
              className="mt-5 w-full rounded-2xl bg-gradient-to-r from-rose-400/90 via-amber-400/88 to-teal-500/88 py-3.5 text-[15px] font-semibold text-gray-950 shadow-lg shadow-teal-500/15 transition hover:brightness-105 active:scale-[0.99]"
              style={{ fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif" }}
            >
              知道了
            </button>
          </div>
        </div>
      ) : null}

      <AnimatePresence>
        {!playing ? (
          <motion.div
            className="fixed inset-0 z-[60] flex items-end justify-center bg-black/55 backdrop-blur-md sm:items-center sm:p-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
            style={{
              paddingLeft: "max(1rem, env(safe-area-inset-left, 0px))",
              paddingRight: "max(1rem, env(safe-area-inset-right, 0px))",
              paddingBottom: "max(0.75rem, env(safe-area-inset-bottom, 0px))",
              paddingTop: "max(0.5rem, env(safe-area-inset-top, 0px))",
            }}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.94, y: 12 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96 }}
              transition={{ type: "spring", stiffness: 380, damping: 28 }}
              className="max-h-[min(88dvh,calc(100dvh-env(safe-area-inset-top)-env(safe-area-inset-bottom)-1.5rem))] w-full max-w-sm overflow-y-auto overscroll-contain rounded-t-[1.5rem] border-[0.5px] border-white/[0.18] border-b-0 bg-white/[0.08] p-5 text-center shadow-[0_24px_80px_rgba(0,0,0,0.55),0_0_0_1px_rgba(255,255,255,0.05)_inset] backdrop-blur-[24px] sm:rounded-[26px] sm:border-b sm:p-7"
              style={{ WebkitBackdropFilter: "blur(24px)" }}
            >
              <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-white/40">Game Over</p>
              <h2 className="mt-2 text-xl font-semibold tracking-tight text-white">越界过久</h2>
              <p className="mt-2 text-[13px] text-white/50">堆叠越过红线并持续 3 秒</p>
              <p className="mt-4 text-3xl font-semibold tabular-nums text-white/95">{score}</p>
              <p className="text-[12px] text-white/40">本局得分</p>
              <div className="mt-6 flex flex-col gap-2">
                <button
                  type="button"
                  onClick={restart}
                  className="w-full rounded-2xl border-0 bg-gradient-to-r from-rose-400 via-amber-400 to-teal-500 py-3 text-[15px] font-semibold text-gray-950 shadow-lg shadow-teal-500/15"
                >
                  重新开始
                </button>
                <button
                  type="button"
                  onClick={() => router.push("/lobby")}
                  className="w-full rounded-2xl border-[0.5px] border-white/15 bg-white/5 py-3 text-[14px] font-medium text-white/80"
                >
                  返回大厅
                </button>
              </div>
              <p className="mt-5 text-[12px] italic text-teal-200/65">Reach Beyond the Stars</p>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
      <LoopingBgmControl src="/audio/games/merge/Velvet_Resonance.mp3" storageKey="bgm-volume:merge" />
    </div>
  )
}
