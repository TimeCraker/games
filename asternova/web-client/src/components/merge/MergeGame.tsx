"use client"

/**
 * AsterNova Merge — Matter.js + Apple 风 UI + Framer Motion
 */

import * as React from "react"
import { Bodies, Body, Composite, Engine, Events, Render, Runner, World } from "matter-js"
import { AnimatePresence, motion } from "framer-motion"
import { arcadeAccentStyle } from "@/src/components/arcade/accent"
import { useArcadeAccent } from "@/src/components/arcade/useArcadeAccent"
import { ArcadeEntry } from "@/src/components/arcade/ArcadeEntry"
import { ArcadeResult } from "@/src/components/arcade/ArcadeResult"
import { BrandMark } from "@/src/components/arcade/BrandMark"
import { HudStat } from "@/src/components/arcade/HudKit"
import { formatScore } from "@/src/components/arcade/records"
import { useArcadeBest } from "@/src/components/arcade/useArcadeRecords"
import { LoopingBgmControl } from "@/src/components/audio/LoopingBgmControl"
import { GameBackButton } from "@/src/components/ui/GameBackButton"
import { StagePortal } from "@/src/components/game-shell/StagePortal"
import { useMobileGameViewport } from "@/src/hooks/useMobileGameViewport"

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
  /** 高光 → 边缘的渐变节点（由下方 tierPalette 的单调坡道生成） */
  highlight: string
  core: string
  mid: string
  rim: string
  edge: string
  glow: string
}

/** 每档的半径与名称（半径越大越难堆稳，名字承载「进化到第几级」的语感） */
const TIER_NAMES = ["星尘", "微光", "流萤", "晨星", "辉星", "琥光", "鎏金", "熔金", "瀚光", "星冕"] as const
const TIER_RADII = [20, 24, 28, 32, 36, 40, 45, 50, 56, 62] as const

/**
 * 每档的 [色相, 饱和度, 明度]。刻意做成「冷灰 → 古铜 → 金 → 白热」四段式，
 * **而不是线性插值** —— 线性从 215° 走到 42° 会经过 120° 绿，
 * 实测渲染出糖果薄荷绿（同属不属于品牌体系的 AI 味）。
 * 故显式给表：1–3 级是低饱和冷灰（矿石感），4 级起跳到暖区，
 * 4–10 级在 58°→30° 的窄暖色带里靠明度(63→91)与饱和(30→60)拉开档次。
 * 全程避开 90–160°（绿）与 270–330°（紫/品红）。
 */
const TIER_RAMP: ReadonlyArray<readonly [number, number, number]> = [
  [210, 12, 44], // 1 星尘 · 冷灰
  [198, 16, 52], // 2 微光 · 钢灰
  [183, 20, 58], // 3 流萤 · 灰青
  [58, 30, 63], // 4 晨星 · 浅古铜
  [53, 40, 68], // 5 辉星
  [48, 48, 72], // 6 琥光
  [43, 55, 77], // 7 鎏金
  [38, 60, 81], // 8 熔金
  [34, 58, 86], // 9 瀚光
  [30, 52, 91], // 10 星冕 · 白热
]

function tierPalette(level: number): Pick<StarTier, "highlight" | "core" | "mid" | "rim" | "edge" | "glow"> {
  const [hue, sat, light] = TIER_RAMP[Math.min(TIER_RAMP.length - 1, Math.max(0, level - 1))]
  const h = (s: number, l: number) =>
    `hsl(${hue}, ${Math.round(Math.min(100, s))}%, ${Math.round(Math.max(0, Math.min(97, l)))}%)`
  const rimLight = Math.max(22, light - 17)
  return {
    highlight: h(sat * 0.5, light + 30),
    core: h(sat * 0.72, light + 18),
    mid: h(sat, light),
    rim: h(sat, rimLight),
    edge: `hsla(${hue}, ${sat}%, ${Math.round(rimLight)}%, 0.9)`,
    glow: `hsla(${hue}, ${sat}%, ${Math.round(Math.min(92, light))}%, 0.46)`,
  }
}

/** 10 档：更大半径 + 每档独立渐变节点 */
export const STAR_TIERS: StarTier[] = TIER_NAMES.map((name, i) => ({
  level: i + 1,
  radius: TIER_RADII[i],
  name,
  ...tierPalette(i + 1),
}))

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
      className="flex w-full flex-col items-center justify-center gap-2.5 rounded-[18px] border border-white/10 bg-white/[0.06] px-3 py-3.5 shadow-[0_1px_0_rgba(255,255,255,0.05)_inset,0_12px_40px_rgba(0,0,0,0.35)] backdrop-blur-[18px] sm:rounded-[20px] sm:py-4 md:min-h-[200px] md:w-[118px]"
      style={{ WebkitBackdropFilter: "blur(18px)" }}
    >
      <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-white/50">下一颗</p>
      <div
        className="relative flex h-[88px] w-[88px] items-center justify-center rounded-2xl border border-white/10 bg-black/25"
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
            boxShadow: `0 0 20px ${tier.glow}, 0 0 36px rgba(216,163,60,0.12), inset 0 0 14px rgba(255,255,255,0.35)`,
            border: "0.5px solid rgba(255,255,255,0.22)",
          }}
        />
      </div>
      <div className="text-center">
        <p className="text-[11px] font-semibold tabular-nums text-white/50">Lv.{tier.level}</p>
        <p className="mt-0.5 text-[13px] font-medium tracking-tight text-white/90">{tier.name}</p>
      </div>
    </div>
  )
}

function MergeIconDrop({ className, iconClass }: { className?: string; iconClass?: string }) {
  return (
    <span
      className={`flex shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-200/40 to-amber-400/28 ${iconClass ?? "h-11 w-11"} ${className ?? ""}`}
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
      className={`flex shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-200/38 to-[#8CBEAA]/26 ${iconClass ?? "h-11 w-11"} ${className ?? ""}`}
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
      className={`flex shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#C08069]/32 to-[#B8724F]/25 ${iconClass ?? "h-11 w-11"} ${className ?? ""}`}
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
      className={`flex shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#A8BED6]/32 to-[#5E7994]/26 ${iconClass ?? "h-11 w-11"} ${className ?? ""}`}
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
  useArcadeAccent("merge")
  const shellRef = React.useRef<HTMLDivElement | null>(null)
  const stageRef = React.useRef<HTMLDivElement | null>(null)
  const engineRef = React.useRef<Engine | null>(null)
  const renderRef = React.useRef<Render | null>(null)
  const runnerRef = React.useRef<Runner | null>(null)

  const [mouseNorm, setMouseNorm] = React.useState({ x: 0.5, y: 0.5 })
  const [score, setScore] = React.useState(0)
  // 历史最高改为读全街机记录总线（此前 only 存在组件 state 里，刷新即丢）
  const best = useArcadeBest("merge")
  const scoreRef = React.useRef(0)
  const [playing, setPlaying] = React.useState(true)
  const [ripples, setRipples] = React.useState<Ripple[]>([])
  const [ghostX, setGhostX] = React.useState(WORLD_W / 2)
  /** SSR/首帧固定为 1，避免与 random 不一致导致 hydration 报错 */
  const [nextLevel, setNextLevel] = React.useState(1)
  const [rulesModalOpen, setRulesModalOpen] = React.useState(true)
  const [dontShowRulesAgain, setDontShowRulesAgain] = React.useState(false)
  // 背景音乐就绪门：音乐未加载完时压住「知道了」按钮
  const [bgmReady, setBgmReady] = React.useState(false)
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

    const { isMobile } = useMobileGameViewport()

const confirmMergeRules = React.useCallback(() => {
    try {
      if (dontShowRulesAgain) localStorage.setItem(MERGE_STORAGE_SKIP_RULES, "1")
    } catch {
      /* ignore */
    }
    setRulesModalOpen(false)
  }, [dontShowRulesAgain])

  // 规则弹层的键盘可达性（焦点陷阱 / Esc = 等同点确认按钮）已移交共享的 ArcadeEntry。
  // Game Over 的焦点陷阱/role 已移交给共享的 ResultOverlay（其内部自带 useDialogA11y，
  // closeOnEsc:false 语义一致），故此处不再单独持有 dialog ref。

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

          setScore((s) => s + nl * nl * 10)
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
      ctx.strokeStyle = "rgba(192, 80, 58, 0.6)"
      ctx.lineWidth = 1.5
      ctx.setLineDash([6, 6])
      ctx.beginPath()
      ctx.moveTo(12, DANGER_Y)
      ctx.lineTo(WORLD_W - 12, DANGER_Y)
      ctx.stroke()
      ctx.setLineDash([])
      ctx.fillStyle = "rgba(192, 80, 58, 0.11)"
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
      className="relative flex h-full min-h-0 min-h-full flex-col overflow-hidden bg-space-black text-white"
      style={arcadeAccentStyle("merge")}
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
          background: `radial-gradient(42rem 42rem at ${mouseNorm.x * 100}% ${mouseNorm.y * 100}%, rgba(216,163,60,0.08), transparent 55%),
            radial-gradient(36rem 36rem at ${mouseNorm.x * 100 + 8}% ${mouseNorm.y * 100 - 5}%, rgba(192,128,105,0.06), transparent 50%)`,
        }}
      />

      {isMobile && !rulesModalOpen && playing ? (
        <StagePortal>
          <button
            type="button"
            onClick={() => setRulesModalOpen(true)}
            className="fixed z-[70] flex min-h-[44px] min-w-[44px] items-center justify-center rounded-full border border-white/10 bg-black/45 px-3.5 text-[13px] font-medium text-white/85 backdrop-blur-md transition hover:bg-white/[0.11] active:scale-[0.98]"
            style={{
              WebkitBackdropFilter: "blur(14px)",
              top: "max(0.75rem, env(safe-area-inset-top, 0px))",
              right: "max(0.75rem, env(safe-area-inset-right, 0px))",
            }}
          >
            规则
          </button>
        </StagePortal>
      ) : !isMobile ? (
        <button
          type="button"
          onClick={() => setRulesModalOpen(true)}
          className="absolute z-30 rounded-full border border-white/10 bg-white/[0.07] px-3 py-1.5 text-[11px] font-medium text-white/80 shadow-[0_8px_28px_rgba(0,0,0,0.35)] backdrop-blur-md transition hover:bg-white/[0.11] active:scale-[0.98] min-[400px]:px-3.5 min-[400px]:text-[12px] sm:right-6 sm:top-6"
          style={{
            WebkitBackdropFilter: "blur(14px)",
            top: "max(0.75rem, env(safe-area-inset-top, 0px))",
            right: "max(0.75rem, env(safe-area-inset-right, 0px))",
          }}
        >
          规则
        </button>
      ) : null}

      <div className="relative z-10 mx-auto flex min-h-0 w-full max-w-[min(100%,42rem)] flex-1 flex-col gap-3 overflow-y-auto overscroll-y-contain px-[max(0.75rem,env(safe-area-inset-left))] pb-[max(0.75rem,env(safe-area-inset-bottom))] pr-[max(0.75rem,env(safe-area-inset-right))] pt-[max(0.35rem,env(safe-area-inset-top))] min-[400px]:gap-4 min-[400px]:px-4 min-[400px]:pb-6 min-[400px]:pt-4 sm:gap-4 sm:pb-6 sm:pt-4 lg:overflow-hidden">
        <motion.header
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-col items-center gap-2 text-center sm:gap-2.5"
        >
          <BrandMark slug="merge" variant="title" as="h2" />
          <p className="max-w-md px-1 text-center text-[12px] font-normal leading-relaxed text-white/50 sm:text-[13px]">
            同级相撞合成升级 · 越红线 3 秒结束 · 点击 / E / 空格下落
          </p>
        </motion.header>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.08, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="relative mx-auto w-full"
        >
          <div
            className="relative overflow-hidden rounded-[22px] border border-white/10 bg-white/[0.04] p-2.5 shadow-[0_1px_0_rgba(255,255,255,0.06)_inset,0_24px_80px_rgba(0,0,0,0.45),0_0_0_1px_rgba(255,255,255,0.03),0_40px_100px_rgba(192,128,105,0.06)] backdrop-blur-[22px] backdrop-saturate-150 sm:rounded-[28px] sm:p-3"
            style={{ WebkitBackdropFilter: "blur(22px) saturate(150%)" }}
          >
            <HudStat
              layout="split"
              className="mb-2 gap-3 px-0.5 sm:mb-3"
              label="得分"
              labelClassName="text-[10px] font-medium uppercase tracking-[0.22em] text-white/50 sm:text-[11px]"
              valueClassName="font-mono-data text-[13px] tabular-nums text-white/85 sm:text-[14px]"
              value={
                <>
                  <span className="text-white/90">{score}</span>
                  <span className="mx-1 text-white/50">/</span>
                  {/* 历史最高来自记录总线（局末才写入），故局中取 max(历史最高, 本局分数)，
                      避免本局已破纪录时显示成「1960 / 最高 960」这种自相矛盾的读数 */}
                  <span className="text-white/50">最高 {formatScore(Math.max(best ?? 0, score))}</span>
                </>
              }
            />

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
                          className="pointer-events-none absolute rounded-full border border-amber-200/30 bg-gradient-to-br from-amber-200/22 to-[#C08069]/16"
                          style={{
                            left: `${((rp.x - rp.r) / WORLD_W) * 100}%`,
                            top: `${((rp.y - rp.r) / WORLD_H) * 100}%`,
                            width: `${((rp.r * 2) / WORLD_W) * 100}%`,
                            height: `${((rp.r * 2) / WORLD_H) * 100}%`,
                            boxShadow:
                              "0 0 28px rgba(216,163,60,0.3), 0 0 52px rgba(192,128,105,0.16), inset 0 0 22px rgba(255,255,255,0.1)",
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
                          boxShadow: `0 0 18px ${previewTier.glow}, 0 0 32px rgba(192,128,105,0.16), inset 0 0 14px rgba(255,255,255,0.32)`,
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

            <p className="mt-2 px-1 text-center text-[10px] font-normal leading-relaxed text-white/50 sm:mt-3 sm:text-[11px]">
              移动准星 · 点击 / E / 空格下落 · 同级两球合成升级
            </p>
          </div>
        </motion.div>

        {isMobile && !rulesModalOpen && playing ? (
          <StagePortal>
            <GameBackButton variant="floating" />
            <div
              className="fixed inset-x-3 z-[70] flex justify-center"
              style={{ bottom: "max(0.75rem, env(safe-area-inset-bottom, 0px))" }}
            >
              <button
                type="button"
                onClick={restart}
                className="min-h-[44px] min-w-[44px] rounded-full border border-white/10 bg-gradient-to-r from-amber-400 via-amber-500 to-amber-600 px-6 py-2.5 text-[13px] font-semibold text-gray-950 shadow-[0_12px_40px_rgba(45,212,191,0.22),0_0_0_1px_rgba(255,255,255,0.15)_inset] transition hover:brightness-105 active:scale-[0.98]"
              >
                再来一局
              </button>
            </div>
          </StagePortal>
        ) : !isMobile ? (
          <div className="flex flex-wrap items-center justify-center gap-2.5 pb-1 sm:gap-3 sm:pb-0">
            <GameBackButton variant="header" />
            <button
              type="button"
              onClick={restart}
              className="min-h-[44px] min-w-[44px] rounded-full border border-white/10 bg-gradient-to-r from-amber-400 via-amber-500 to-amber-600 px-5 py-2.5 text-[12px] font-semibold text-gray-950 shadow-[0_12px_40px_rgba(45,212,191,0.22),0_0_0_1px_rgba(255,255,255,0.15)_inset] transition hover:brightness-105 active:scale-[0.98] sm:min-h-0 sm:px-6 sm:text-[13px]"
            >
              再来一局
            </button>
          </div>
        ) : null}
      </div>

      {rulesModalOpen ? (
        <ArcadeEntry
          slug="merge"
          titleId="merge-rules-title"
          label="知道了"
          onConfirm={confirmMergeRules}
          confirmPending={!bgmReady}
          onRequestClose={confirmMergeRules}
          overlayZClassName="z-[55]"
          safeArea
          skipRules={{
            checked: dontShowRulesAgain,
            onChange: setDontShowRulesAgain,
          }}
        >
            <ul className="mt-5 space-y-4 text-[14px] leading-relaxed text-white/80">
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <MergeIconDrop />
                <div>
                  <div className="font-medium text-white/95">下落</div>
                  <div className="mt-0.5 text-[13px] text-white/55">
                    在画面上移动准星；<span className="text-hud-accent-bright">点击</span>、按{" "}
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
                    两颗<span className="text-[#8CBEAA]">相同等级</span>的球相撞会合成更高一级，并获得分数。
                  </div>
                </div>
              </li>
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <MergeIconDanger />
                <div>
                  <div className="font-medium text-white/95">警戒线</div>
                  <div className="mt-0.5 text-[13px] text-white/55">
                    堆叠超过顶部<span className="text-[#D98A72]">红色虚线</span>并持续约 3 秒，本局结束。
                  </div>
                </div>
              </li>
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <MergeIconNext />
                <div>
                  <div className="font-medium text-white/95">下一颗</div>
                  <div className="mt-0.5 text-[13px] text-white/55">
                    右侧卡片预览下一颗球的等级与配色；共 10 档，从星尘到星冕。
                    <span className="mt-1 block text-[12px] text-white/50">
                      得分较高时，有小概率直接掉落 Lv4–7 大号赠送球。
                    </span>
                  </div>
                </div>
              </li>
            </ul>
        </ArcadeEntry>
      ) : null}

      <StagePortal>
        <AnimatePresence>
          {!playing ? (
            <ArcadeResult
              slug="merge"
              score={score}
              title="OVERFLOW"
              subtitle="越界过久 · 堆叠越过红线并持续 3 秒"
              actionLabel="重新开始"
              onAction={restart}
            />
          ) : null}
        </AnimatePresence>
      </StagePortal>
      <LoopingBgmControl src="/audio/games/merge/Velvet_Resonance.mp3" storageKey="bgm-volume:merge" hidden={rulesModalOpen || !playing} onReady={() => setBgmReady(true)} />
    </div>
  )
}