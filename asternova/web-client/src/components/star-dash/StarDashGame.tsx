"use client"

/**
 * AsterNova - Star Dash
 * Canvas 无限跑酷：双段跳、滑铲、视差星空、粉紫霓虹美学。
 * 游戏状态全部放在 ref 中，由 requestAnimationFrame 驱动，避免每帧 setState。
 */

import * as React from "react"
import { useRouter } from "next/navigation"
import { LoopingBgmControl } from "@/src/components/audio/LoopingBgmControl"

// —— 可调参数 ——
const GRAVITY = 2600
const JUMP_VELOCITY = -720
const BASE_SCROLL = 320
const MAX_SCROLL = 720
const SCROLL_RAMP_PER_SEC = 18
const GROUND_MARGIN = 100
const PLAYER_X = 110
const PLAYER_W = 46
const PLAYER_H_STAND = 62
const PLAYER_H_SLIDE = 30
const SLIDE_DURATION_SEC = 0.8
const OBSTACLE_MIN_GAP = 1.05
const OBSTACLE_MAX_GAP = 2.0
const STAR_MIN_GAP = 0.32
const STAR_MAX_GAP = 0.95
const STARS_PER_BOOST = 10
const BOOST_DURATION_SEC = 3.8
const BOOST_SCROLL_MULT = 1.45
const MAGNET_DURATION_SEC = 9
const MAGNET_PULL = 520
const MAGNET_RADIUS = 210
const POWERUP_INTERVAL_SEC = 20
const STORAGE_SKIP_RULES = "star-dash-skip-rules"

const OVERHANG_SPAWN_WEIGHT = 0.26

type GameMode = "start" | "playing" | "over"

type Obstacle = { x: number; y: number; w: number; h: number; kind: "normal" | "overhang" }
type StarDust = { x: number; y: number; r: number; taken: boolean }
type PowerUp = { x: number; y: number; kind: "magnet" | "shield"; r: number; taken: boolean }
type Particle = { x: number; y: number; vx: number; vy: number; life: number; maxLife: number }
type TrailSeg = { x: number; y: number; h: number; alpha: number }

type GameState = {
  mode: GameMode
  /** 像素，地面线 Y（角色脚底对齐） */
  groundY: number
  playerY: number
  velY: number
  jumpsLeft: number
  slideEndAt: number
  scroll: number
  distance: number
  scoreStars: number
  /** 再吃满 10 颗可手动触发星爆加速 */
  starsTowardBoost: number
  /** 已满 10 星，等待玩家点按钮 / 按 E */
  boostReady: boolean
  boostEndAt: number
  magnetEndAt: number
  shieldCharges: number
  nextPowerUpAt: number
  obstacles: Obstacle[]
  stars: StarDust[]
  powerUps: PowerUp[]
  particles: Particle[]
  trail: TrailSeg[]
  nextObstacleIn: number
  nextStarIn: number
  timePlaying: number
  /** 触摸滑铲 */
  touchStartY: number | null
  width: number
  height: number
  dpr: number
  /** 视差层偏移 */
  paraFar: number
  paraNear: number
  starsFar: { x: number; y: number; s: number; a: number }[]
  starsNear: { x: number; y: number; s: number; a: number }[]
  tapPulse: number
}

function initStarField(
  count: number,
  w: number,
  h: number,
): { x: number; y: number; s: number; a: number }[] {
  const out: { x: number; y: number; s: number; a: number }[] = []
  for (let i = 0; i < count; i++) {
    out.push({
      x: Math.random() * w * 2,
      y: Math.random() * h * 0.75,
      s: Math.random() * 1.8 + 0.4,
      a: Math.random() * 0.5 + 0.2,
    })
  }
  return out
}

function aabbOverlap(
  ax: number,
  ay: number,
  aw: number,
  ah: number,
  bx: number,
  by: number,
  bw: number,
  bh: number,
) {
  return ax < bx + bw && ax + aw > bx && ay < by + bh && ay + ah > by
}

/** 星尘 / 道具的纵向范围：从二段跳顶点一带到接近地面（canvas Y 向下增大） */
function randomCollectibleY(groundY: number) {
  const standTop = groundY - PLAYER_H_STAND
  const yHigh = standTop - 135
  const yLow = groundY - 22
  const span = Math.max(40, yLow - yHigh)
  return yHigh + Math.random() * span
}

function circleRectOverlap(cx: number, cy: number, cr: number, rx: number, ry: number, rw: number, rh: number) {
  const nx = Math.max(rx, Math.min(cx, rx + rw))
  const ny = Math.max(ry, Math.min(cy, ry + rh))
  const dx = cx - nx
  const dy = cy - ny
  return dx * dx + dy * dy < cr * cr
}

/** 兼容无 roundRect 的环境 */
function fillRoundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  const rr = Math.min(r, w / 2, h / 2)
  ctx.beginPath()
  ctx.moveTo(x + rr, y)
  ctx.arcTo(x + w, y, x + w, y + h, rr)
  ctx.arcTo(x + w, y + h, x, y + h, rr)
  ctx.arcTo(x, y + h, x, y, rr)
  ctx.arcTo(x, y, x + w, y, rr)
  ctx.closePath()
  ctx.fill()
}

function strokeRoundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  const rr = Math.min(r, w / 2, h / 2)
  ctx.beginPath()
  ctx.moveTo(x + rr, y)
  ctx.arcTo(x + w, y, x + w, y + h, rr)
  ctx.arcTo(x + w, y + h, x, y + h, rr)
  ctx.arcTo(x, y + h, x, y, rr)
  ctx.arcTo(x, y, x + w, y, rr)
  ctx.closePath()
  ctx.stroke()
}

/** 与规则卡片一致的圆角渐变底 + 白色线稿图标 */
function DashIconJump({ className, iconClass }: { className?: string; iconClass?: string }) {
  return (
    <span
      className={`flex shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-pink-300/40 to-violet-500/35 ${iconClass ?? "h-11 w-11"} ${className ?? ""}`}
      aria-hidden
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-white">
        <path
          d="M6.5 17.5L15.5 8.5M15.5 8.5H11M15.5 8.5V13"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity={0.9}
        />
        <path
          d="M9.5 17.5L18.5 8.5M18.5 8.5H14.2M18.5 8.5V12.8"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  )
}

function DashIconSlide({ className, iconClass }: { className?: string; iconClass?: string }) {
  return (
    <span
      className={`flex shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-fuchsia-300/35 to-purple-600/35 ${iconClass ?? "h-11 w-11"} ${className ?? ""}`}
      aria-hidden
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-white">
        <path
          d="M7 7C7 7 10 10 12.5 13.5C14.5 16.3 16.5 17.5 18.5 17.5"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M15.5 15.5L18.5 17.5L16.8 19.8"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  )
}

function DashIconStarBurst({ className, iconClass }: { className?: string; iconClass?: string }) {
  return (
    <span
      className={`flex shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-200/35 to-orange-400/30 ${iconClass ?? "h-11 w-11"} ${className ?? ""}`}
      aria-hidden
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className="text-white">
        <path
          d="M12 4.5L13.8 9.9L19.5 12L13.8 14.1L12 19.5L10.2 14.1L4.5 12L10.2 9.9L12 4.5Z"
          stroke="currentColor"
          strokeWidth="1.45"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  )
}

export function StarDashGame() {
  const router = useRouter()
  const wrapRef = React.useRef<HTMLDivElement | null>(null)
  const canvasRef = React.useRef<HTMLCanvasElement | null>(null)
  const rafRef = React.useRef<number | null>(null)
  const stateRef = React.useRef<GameState | null>(null)
  const lastTsRef = React.useRef<number>(0)
  const prevModeRef = React.useRef<GameMode>("start")
  const [isGameOver, setIsGameOver] = React.useState(false)
  const [screenMode, setScreenMode] = React.useState<GameMode>("start")
  const [rulesModalOpen, setRulesModalOpen] = React.useState(true)
  const [dontShowRulesAgain, setDontShowRulesAgain] = React.useState(false)
  const [boostReadyUi, setBoostReadyUi] = React.useState(false)
  const prevBoostReadyRef = React.useRef(false)

  const resizeCanvas = React.useCallback(() => {
    const canvas = canvasRef.current
    const wrap = wrapRef.current
    if (!canvas || !wrap) return
    const rect = wrap.getBoundingClientRect()
    const dpr = Math.min(2, window.devicePixelRatio || 1)
    const w = Math.max(320, Math.floor(rect.width))
    const h = Math.max(400, Math.floor(rect.height))
    canvas.width = Math.floor(w * dpr)
    canvas.height = Math.floor(h * dpr)
    canvas.style.width = `${w}px`
    canvas.style.height = `${h}px`
    const ctx = canvas.getContext("2d")
    if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

    const s = stateRef.current
    if (s) {
      s.width = w
      s.height = h
      s.dpr = dpr
      s.groundY = h - GROUND_MARGIN
    }
  }, [])

  const resetPlayingState = React.useCallback((s: GameState) => {
    s.mode = "playing"
    s.playerY = s.groundY - PLAYER_H_STAND
    s.velY = 0
    s.jumpsLeft = 2
    s.slideEndAt = 0
    s.scroll = BASE_SCROLL
    s.distance = 0
    s.scoreStars = 0
    s.starsTowardBoost = STARS_PER_BOOST
    s.boostReady = false
    s.boostEndAt = 0
    s.magnetEndAt = 0
    s.shieldCharges = 0
    s.nextPowerUpAt = POWERUP_INTERVAL_SEC
    s.obstacles = []
    s.stars = []
    s.powerUps = []
    s.particles = []
    s.trail = []
    s.nextObstacleIn = 0.8
    s.nextStarIn = 0.4
    s.timePlaying = 0
    s.touchStartY = null
    setIsGameOver(false)
  }, [])

  const tryJump = React.useCallback(() => {
    const s = stateRef.current
    if (!s) return
    if (s.mode === "start") {
      resetPlayingState(s)
      return
    }
    if (s.mode === "over") {
      resetPlayingState(s)
      return
    }
    if (s.mode !== "playing") return
    if (s.jumpsLeft <= 0) return
    s.velY = JUMP_VELOCITY
    s.jumpsLeft -= 1
  }, [resetPlayingState])

  const trySlide = React.useCallback(() => {
    const s = stateRef.current
    if (!s || s.mode !== "playing") return
    const now = performance.now() / 1000
    s.slideEndAt = now + SLIDE_DURATION_SEC
  }, [])

  const tryActivateBoost = React.useCallback(() => {
    const s = stateRef.current
    if (!s || s.mode !== "playing" || !s.boostReady) return
    s.boostReady = false
    s.boostEndAt = performance.now() / 1000 + BOOST_DURATION_SEC
  }, [])

  const confirmRules = React.useCallback(() => {
    try {
      if (dontShowRulesAgain) localStorage.setItem(STORAGE_SKIP_RULES, "1")
    } catch {
      /* ignore */
    }
    try {
      if (typeof window !== "undefined" && window.matchMedia("(max-width: 768px)").matches) {
        const o = (window.screen?.orientation ?? null) as (ScreenOrientation & { lock?: (l: string) => Promise<void> }) | null
        if (o?.lock) {
          void o.lock("landscape").catch(() => {})
        }
      }
    } catch {
      /* ignore */
    }
    setRulesModalOpen(false)
  }, [dontShowRulesAgain])

  React.useLayoutEffect(() => {
    try {
      if (localStorage.getItem(STORAGE_SKIP_RULES) === "1") setRulesModalOpen(false)
    } catch {
      /* ignore */
    }
  }, [])

  React.useEffect(() => {
    const wrap = wrapRef.current
    const canvas = canvasRef.current
    if (!wrap || !canvas) return

    const rect = wrap.getBoundingClientRect()
    const w = Math.max(320, Math.floor(rect.width || wrap.clientWidth || 800))
    // IMPORTANT: use wrap height (not window.innerHeight) so portrait-rotate shell is correctly accounted
    const h = Math.max(400, Math.min(640, Math.floor(rect.height || 600)))
    const dpr = Math.min(2, window.devicePixelRatio || 1)

    const groundY = h - GROUND_MARGIN
    stateRef.current = {
      mode: "start",
      groundY,
      playerY: groundY - PLAYER_H_STAND,
      velY: 0,
      jumpsLeft: 2,
      slideEndAt: 0,
      scroll: BASE_SCROLL,
      distance: 0,
      scoreStars: 0,
      starsTowardBoost: STARS_PER_BOOST,
      boostReady: false,
      boostEndAt: 0,
      magnetEndAt: 0,
      shieldCharges: 0,
      nextPowerUpAt: POWERUP_INTERVAL_SEC,
      obstacles: [],
      stars: [],
      powerUps: [],
      particles: [],
      trail: [],
      nextObstacleIn: 1,
      nextStarIn: 0.5,
      timePlaying: 0,
      touchStartY: null,
      width: w,
      height: h,
      dpr,
      paraFar: 0,
      paraNear: 0,
      starsFar: initStarField(90, w, h),
      starsNear: initStarField(55, w, h),
      tapPulse: 0,
    }

    prevModeRef.current = "start"
    setIsGameOver(false)

    resizeCanvas()

    const ro = new ResizeObserver(() => resizeCanvas())
    ro.observe(wrap)

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space") {
        e.preventDefault()
        tryJump()
      } else if (e.code === "ArrowDown") {
        e.preventDefault()
        trySlide()
      } else if (e.code === "KeyE") {
        e.preventDefault()
        tryActivateBoost()
      }
    }

    window.addEventListener("keydown", onKeyDown)

    const loop = (ts: number) => {
      const s = stateRef.current
      const cvs = canvasRef.current
      if (!s || !cvs) {
        rafRef.current = requestAnimationFrame(loop)
        return
      }
      const ctx = cvs.getContext("2d")
      if (!ctx) {
        rafRef.current = requestAnimationFrame(loop)
        return
      }

      if (!lastTsRef.current) lastTsRef.current = ts
      const dt = Math.min((ts - lastTsRef.current) / 1000, 0.05)
      lastTsRef.current = ts

      const w = s.width
      const h = s.height
      const nowSec = ts / 1000

      if (s.mode !== prevModeRef.current) {
        prevModeRef.current = s.mode
        setIsGameOver(s.mode === "over")
        setScreenMode(s.mode)
        if (s.mode !== "playing") {
          prevBoostReadyRef.current = false
          setBoostReadyUi(false)
        }
      }

      if (s.mode === "playing" && s.boostReady !== prevBoostReadyRef.current) {
        prevBoostReadyRef.current = s.boostReady
        setBoostReadyUi(s.boostReady)
      }

      // —— 更新 ——
      s.tapPulse += dt * 3.5

      if (s.mode === "start" || s.mode === "over") {
        s.paraFar += dt * 40
        s.paraNear += dt * 90
      }

      if (s.mode === "playing") {
        s.timePlaying += dt
        s.scroll = Math.min(MAX_SCROLL, BASE_SCROLL + s.timePlaying * SCROLL_RAMP_PER_SEC)
        const boostOn = nowSec < s.boostEndAt
        const scrollMul = boostOn ? BOOST_SCROLL_MULT : 1
        const effScroll = s.scroll * scrollMul
        s.distance += (effScroll * dt) / 10

        const sliding = nowSec < s.slideEndAt
        const ph = sliding ? PLAYER_H_SLIDE : PLAYER_H_STAND
        const px = PLAYER_X
        const groundTop = s.groundY - ph
        const magnetOn = nowSec < s.magnetEndAt
        const pw = PLAYER_W
        const pcx = px + pw * 0.5
        const pcy = s.playerY + ph * 0.5

        s.velY += GRAVITY * dt
        s.playerY += s.velY * dt

        if (s.playerY >= groundTop) {
          s.playerY = groundTop
          s.velY = 0
          s.jumpsLeft = 2
        }

        if (sliding) {
          s.trail.push({ x: px, y: s.playerY, h: ph, alpha: 0.85 })
          if (s.trail.length > 14) s.trail.shift()
        } else {
          s.trail = s.trail.map((t) => ({ ...t, alpha: t.alpha - dt * 2.5 })).filter((t) => t.alpha > 0.02)
        }

        s.paraFar += dt * effScroll * 0.08
        s.paraNear += dt * effScroll * 0.18

        s.nextObstacleIn -= dt
        if (s.nextObstacleIn <= 0) {
          if (Math.random() < OVERHANG_SPAWN_WEIGHT) {
            const bw = 38 + Math.random() * 26
            const bh = 30 + Math.random() * 12
            const bottom = s.groundY - PLAYER_H_STAND - 4
            s.obstacles.push({ x: w + 30, y: bottom - bh, w: bw, h: bh, kind: "overhang" })
          } else {
            const obsH = 36 + Math.random() * 48
            const obsW = 28 + Math.random() * 22
            const onGround = Math.random() > 0.38
            const oy = onGround ? s.groundY - obsH : s.groundY - obsH - 85 - Math.random() * 95
            s.obstacles.push({ x: w + 30, y: oy, w: obsW, h: obsH, kind: "normal" })
          }
          s.nextObstacleIn = OBSTACLE_MIN_GAP + Math.random() * (OBSTACLE_MAX_GAP - OBSTACLE_MIN_GAP)
        }

        s.nextStarIn -= dt
        if (s.nextStarIn <= 0) {
          const sy = randomCollectibleY(s.groundY)
          s.stars.push({ x: w + 24, y: sy, r: 7 + Math.random() * 5, taken: false })
          s.nextStarIn = STAR_MIN_GAP + Math.random() * (STAR_MAX_GAP - STAR_MIN_GAP)
        }

        while (s.timePlaying >= s.nextPowerUpAt) {
          const kind: PowerUp["kind"] = Math.random() < 0.5 ? "magnet" : "shield"
          const py = randomCollectibleY(s.groundY)
          s.powerUps.push({ x: w + 44, y: py, kind, r: 17, taken: false })
          s.nextPowerUpAt += POWERUP_INTERVAL_SEC
        }

        for (const st of s.stars) {
          if (st.taken) continue
          if (magnetOn) {
            const dx = pcx - st.x
            const dy = pcy - st.y
            const dist = Math.hypot(dx, dy)
            if (dist < MAGNET_RADIUS && dist > 6) {
              const pull = (MAGNET_PULL * dt) / Math.max(dist, 1)
              st.x += dx * pull
              st.y += dy * pull
            }
          }
        }

        for (const o of s.obstacles) o.x -= effScroll * dt
        for (const st of s.stars) if (!st.taken) st.x -= effScroll * dt
        for (const pu of s.powerUps) if (!pu.taken) pu.x -= effScroll * dt
        s.obstacles = s.obstacles.filter((o) => o.x + o.w > -20)
        s.powerUps = s.powerUps.filter((p) => !p.taken && p.x + p.r > -10)

        const burstAt = (cx: number, cy: number, n: number, spread: number) => {
          for (let i = 0; i < n; i++) {
            const ang = (Math.PI * 2 * i) / n + Math.random() * 0.2
            s.particles.push({
              x: cx,
              y: cy,
              vx: Math.cos(ang) * spread * (0.6 + Math.random() * 0.5),
              vy: Math.sin(ang) * spread * (0.6 + Math.random() * 0.5),
              life: 0.4 + Math.random() * 0.25,
              maxLife: 0.55,
            })
          }
        }

        for (const st of s.stars) {
          if (st.taken) continue
          if (circleRectOverlap(st.x, st.y, st.r + 2, px, s.playerY, pw, ph)) {
            st.taken = true
            s.scoreStars += 1
            s.starsTowardBoost -= 1
            if (s.starsTowardBoost <= 0) {
              s.starsTowardBoost = STARS_PER_BOOST
              s.boostReady = true
            }
            burstAt(st.x, st.y, 12, 140)
          }
        }

        for (const pu of s.powerUps) {
          if (pu.taken) continue
          if (circleRectOverlap(pu.x, pu.y, pu.r, px, s.playerY, pw, ph)) {
            pu.taken = true
            if (pu.kind === "magnet") {
              s.magnetEndAt = nowSec + MAGNET_DURATION_SEC
              burstAt(pu.x, pu.y, 14, 100)
            } else {
              s.shieldCharges = Math.min(1, s.shieldCharges + 1)
              burstAt(pu.x, pu.y, 10, 90)
            }
          }
        }

        for (let i = s.obstacles.length - 1; i >= 0; i--) {
          const o = s.obstacles[i]
          if (!aabbOverlap(px, s.playerY, pw, ph, o.x, o.y, o.w, o.h)) continue
          if (boostOn) {
            burstAt(o.x + o.w * 0.5, o.y + o.h * 0.5, 8, 160)
            s.obstacles.splice(i, 1)
            continue
          }
          if (s.shieldCharges > 0) {
            s.shieldCharges -= 1
            burstAt(o.x + o.w * 0.5, o.y + o.h * 0.5, 16, 200)
            s.obstacles.splice(i, 1)
            continue
          }
          s.mode = "over"
          break
        }

        for (const p of s.particles) {
          p.x += p.vx * dt
          p.y += p.vy * dt
          p.vy += 400 * dt
          p.life -= dt
        }
        s.particles = s.particles.filter((p) => p.life > 0)
        s.stars = s.stars.filter((st) => !st.taken && st.x + st.r > -30)
      }

      // —— 绘制 ——
      ctx.clearRect(0, 0, w, h)

      const drawParallaxStars = (offset: number, field: typeof s.starsFar, speedMul: number, twinkle: boolean) => {
        const wrapW = w + 80
        for (const st of field) {
          let sx = (st.x - offset * speedMul) % wrapW
          if (sx < 0) sx += wrapW
          ctx.globalAlpha = st.a * (twinkle ? 0.75 + 0.25 * Math.sin(ts * 0.004 + st.x) : 1)
          ctx.fillStyle = "#e8e4ff"
          ctx.beginPath()
          ctx.arc(sx, st.y, st.s, 0, Math.PI * 2)
          ctx.fill()
        }
        ctx.globalAlpha = 1
      }

      ctx.fillStyle = "#06060f"
      ctx.fillRect(0, 0, w, h)
      const g = ctx.createLinearGradient(0, 0, 0, h)
      g.addColorStop(0, "#0a0614")
      g.addColorStop(0.55, "#0d0820")
      g.addColorStop(1, "#12081c")
      ctx.fillStyle = g
      ctx.fillRect(0, 0, w, h)

      drawParallaxStars(s.paraFar, s.starsFar, 0.12, true)
      drawParallaxStars(s.paraNear, s.starsNear, 0.22, false)

      ctx.strokeStyle = "rgba(168, 85, 247, 0.25)"
      ctx.lineWidth = 2
      ctx.shadowColor = "rgba(236, 72, 153, 0.4)"
      ctx.shadowBlur = 12
      ctx.beginPath()
      ctx.moveTo(0, s.groundY)
      ctx.lineTo(w, s.groundY)
      ctx.stroke()
      ctx.shadowBlur = 0

      const sliding = s.mode === "playing" && nowSec < s.slideEndAt
      const ph = s.mode === "playing" ? (sliding ? PLAYER_H_SLIDE : PLAYER_H_STAND) : PLAYER_H_STAND
      const px = PLAYER_X
      const py = s.playerY
      const boostOnDraw = s.mode === "playing" && nowSec < s.boostEndAt
      const magnetOnDraw = s.mode === "playing" && nowSec < s.magnetEndAt

      if (s.mode === "playing") {
        for (const tr of s.trail) {
          ctx.globalAlpha = tr.alpha * 0.45
          const lg = ctx.createLinearGradient(tr.x, tr.y, tr.x + PLAYER_W, tr.y + tr.h)
          lg.addColorStop(0, "rgba(255, 182, 232, 0.5)")
          lg.addColorStop(0.5, "rgba(216, 180, 254, 0.45)")
          lg.addColorStop(1, "rgba(167, 139, 250, 0.35)")
          ctx.fillStyle = lg
          fillRoundRect(ctx, tr.x, tr.y, PLAYER_W, tr.h, 10)
        }
        ctx.globalAlpha = 1
      }

      for (const o of s.obstacles) {
        ctx.save()
        if (boostOnDraw) {
          ctx.shadowColor = "rgba(253, 186, 116, 0.95)"
          ctx.shadowBlur = 26
        } else {
          ctx.shadowColor = "rgba(244, 114, 182, 0.9)"
          ctx.shadowBlur = o.kind === "overhang" ? 20 : 16
        }
        const og = ctx.createLinearGradient(o.x, o.y, o.x + o.w, o.y + o.h)
        if (boostOnDraw) {
          og.addColorStop(0, "rgba(254, 215, 170, 0.95)")
          og.addColorStop(0.5, "rgba(251, 113, 133, 0.88)")
          og.addColorStop(1, "rgba(192, 132, 252, 0.82)")
        } else {
          og.addColorStop(0, "rgba(251, 207, 232, 0.95)")
          og.addColorStop(0.5, "rgba(192, 132, 252, 0.85)")
          og.addColorStop(1, "rgba(139, 92, 246, 0.75)")
        }
        ctx.fillStyle = og
        ctx.strokeStyle = boostOnDraw ? "rgba(255, 248, 220, 0.55)" : "rgba(255, 255, 255, 0.35)"
        ctx.lineWidth = boostOnDraw ? 2 : 1.5
        fillRoundRect(ctx, o.x, o.y, o.w, o.h, 6)
        strokeRoundRect(ctx, o.x, o.y, o.w, o.h, 6)
        ctx.restore()
      }

      if (boostOnDraw) {
        ctx.save()
        ctx.globalAlpha = 0.18 + 0.07 * Math.sin(ts * 0.014)
        const wg = ctx.createLinearGradient(0, 0, w, h)
        wg.addColorStop(0, "rgba(251, 113, 133, 0.55)")
        wg.addColorStop(0.45, "rgba(217, 70, 239, 0.4)")
        wg.addColorStop(1, "rgba(99, 102, 241, 0.5)")
        ctx.fillStyle = wg
        ctx.fillRect(0, 0, w, h)
        ctx.globalAlpha = 0.35
        ctx.strokeStyle = "rgba(255,255,255,0.12)"
        ctx.lineWidth = 1
        for (let i = 0; i < 8; i++) {
          const sx = ((ts * 0.08 + i * 130) % (w + 200)) - 100
          ctx.beginPath()
          ctx.moveTo(sx, 0)
          ctx.lineTo(sx - 60, h)
          ctx.stroke()
        }
        ctx.restore()
      }

      for (const pu of s.powerUps) {
        if (pu.taken) continue
        ctx.save()
        if (pu.kind === "magnet") {
          ctx.shadowColor = "rgba(244, 114, 182, 0.95)"
          ctx.shadowBlur = 20
          ctx.strokeStyle = "rgba(252, 231, 243, 0.9)"
          ctx.lineWidth = 2.5
          ctx.beginPath()
          ctx.arc(pu.x, pu.y, pu.r, 0, Math.PI * 2)
          ctx.stroke()
          ctx.beginPath()
          ctx.arc(pu.x - 5, pu.y - 2, pu.r * 0.45, 0.3, Math.PI * 1.2)
          ctx.stroke()
          ctx.beginPath()
          ctx.arc(pu.x + 6, pu.y + 3, pu.r * 0.35, -0.5, Math.PI)
          ctx.stroke()
        } else {
          ctx.shadowColor = "rgba(125, 211, 252, 0.9)"
          ctx.shadowBlur = 18
          const sg = ctx.createRadialGradient(pu.x, pu.y, 0, pu.x, pu.y, pu.r)
          sg.addColorStop(0, "rgba(224, 242, 254, 0.95)")
          sg.addColorStop(0.5, "rgba(125, 211, 252, 0.5)")
          sg.addColorStop(1, "rgba(59, 130, 246, 0.25)")
          ctx.fillStyle = sg
          ctx.beginPath()
          ctx.moveTo(pu.x, pu.y - pu.r * 0.85)
          ctx.lineTo(pu.x + pu.r * 0.75, pu.y - pu.r * 0.2)
          ctx.lineTo(pu.x + pu.r * 0.45, pu.y + pu.r * 0.9)
          ctx.lineTo(pu.x - pu.r * 0.45, pu.y + pu.r * 0.9)
          ctx.lineTo(pu.x - pu.r * 0.75, pu.y - pu.r * 0.2)
          ctx.closePath()
          ctx.fill()
          ctx.strokeStyle = "rgba(255,255,255,0.5)"
          ctx.lineWidth = 1.5
          ctx.stroke()
        }
        ctx.restore()
      }

      for (const st of s.stars) {
        if (st.taken) continue
        ctx.save()
        ctx.shadowColor = "rgba(252, 211, 77, 0.95)"
        ctx.shadowBlur = 14
        const sg = ctx.createRadialGradient(st.x, st.y, 0, st.x, st.y, st.r * 2)
        sg.addColorStop(0, "#fff7ed")
        sg.addColorStop(0.35, "#fbcfe8")
        sg.addColorStop(0.7, "#c084fc")
        sg.addColorStop(1, "rgba(139, 92, 246, 0.2)")
        ctx.fillStyle = sg
        ctx.beginPath()
        ctx.arc(st.x, st.y, st.r, 0, Math.PI * 2)
        ctx.fill()
        ctx.restore()
      }

      for (const p of s.particles) {
        const t = p.life / p.maxLife
        ctx.globalAlpha = Math.max(0, t)
        ctx.fillStyle = `rgba(244, 182, 232, ${0.4 + t * 0.5})`
        ctx.beginPath()
        ctx.arc(p.x, p.y, 4 * t, 0, Math.PI * 2)
        ctx.fill()
      }
      ctx.globalAlpha = 1

      ctx.save()
      ctx.shadowColor = "rgba(236, 72, 153, 0.75)"
      ctx.shadowBlur = 22
      const pg = ctx.createLinearGradient(px, py, px + PLAYER_W, py + ph)
      pg.addColorStop(0, "#ffe4f0")
      pg.addColorStop(0.45, "#f0abfc")
      pg.addColorStop(1, "#a78bfa")
      ctx.fillStyle = pg
      ctx.strokeStyle = "rgba(255,255,255,0.5)"
      ctx.lineWidth = 2
      fillRoundRect(ctx, px, py, PLAYER_W, ph, 12)
      strokeRoundRect(ctx, px, py, PLAYER_W, ph, 12)
      ctx.restore()

      if (s.mode === "playing") {
        ctx.font = "600 14px system-ui, -apple-system, sans-serif"
        ctx.fillStyle = "rgba(255,255,255,0.92)"
        ctx.textAlign = "right"
        const meters = Math.floor(s.distance + s.scoreStars * 12)
        ctx.fillText(`${meters} m`, w - 18, 36)
        ctx.font = "11px system-ui, -apple-system, sans-serif"
        ctx.fillStyle = "rgba(255,255,255,0.5)"
        ctx.fillText(`星尘 × ${s.scoreStars}`, w - 18, 52)
        let lineY = 68
        if (s.boostReady) {
          ctx.fillStyle = "rgba(253, 186, 116, 0.95)"
          ctx.fillText("星爆就绪 · 点「星爆」或按 E", w - 18, lineY)
        } else {
          ctx.fillStyle = "rgba(251, 207, 232, 0.78)"
          ctx.fillText(`再 ${s.starsTowardBoost} 颗 → 星爆加速`, w - 18, lineY)
        }
        lineY += 16
        if (boostOnDraw) {
          ctx.fillStyle = "rgba(253, 186, 116, 0.9)"
          ctx.fillText("★ 无敌加速中", w - 18, lineY)
          lineY += 16
        }
        if (magnetOnDraw) {
          ctx.fillStyle = "rgba(244, 114, 182, 0.85)"
          ctx.fillText("磁吸星尘", w - 18, lineY)
          lineY += 16
        }
        if (s.shieldCharges > 0) {
          ctx.fillStyle = "rgba(125, 211, 252, 0.9)"
          ctx.fillText(`护盾 × ${s.shieldCharges}`, w - 18, lineY)
        }
      }

      if (s.mode === "start") {
        ctx.textAlign = "center"
        ctx.font = "700 26px system-ui, sans-serif"
        const tg = ctx.createLinearGradient(w / 2 - 160, 0, w / 2 + 160, 0)
        tg.addColorStop(0, "#fda4c6")
        tg.addColorStop(0.5, "#e879f9")
        tg.addColorStop(1, "#8b5cf6")
        ctx.fillStyle = tg
        ctx.shadowColor = "rgba(232, 121, 249, 0.55)"
        ctx.shadowBlur = 28
        ctx.fillText("AsterNova - Star Dash", w / 2, h * 0.34)
        ctx.shadowBlur = 0
        ctx.font = "13px system-ui, sans-serif"
        ctx.fillStyle = "rgba(255,255,255,0.5)"
        ctx.fillText("Let's Running", w / 2, h * 0.34 + 28)

        const pulse = 0.55 + 0.45 * Math.sin(s.tapPulse)
        ctx.globalAlpha = pulse
        ctx.font = "600 15px system-ui, sans-serif"
        ctx.fillStyle = "#f9a8d4"
        ctx.fillText("点击 / 空格 · Tap to Start", w / 2, h * 0.55)
        ctx.globalAlpha = 1
        ctx.font = "12px system-ui, sans-serif"
        ctx.fillStyle = "rgba(255,255,255,0.35)"
        ctx.fillText("二段跳 · 松手后下滑 / ↓ 滑铲", w / 2, h * 0.62)
      }

      if (s.mode === "over") {
        ctx.fillStyle = "rgba(0,0,0,0.55)"
        ctx.fillRect(0, 0, w, h)
        ctx.textAlign = "center"
        ctx.font = "700 22px system-ui, sans-serif"
        ctx.fillStyle = "#fce7f3"
        ctx.fillText("Game Over", w / 2, h * 0.38)
        const finalScore = Math.floor(s.distance + s.scoreStars * 12)
        ctx.font = "16px system-ui, sans-serif"
        ctx.fillStyle = "rgba(255,255,255,0.85)"
        ctx.fillText(`最终距离 ${finalScore} m · 星尘 ${s.scoreStars}`, w / 2, h * 0.46)
        ctx.font = "italic 15px system-ui, sans-serif"
        const sg = ctx.createLinearGradient(w / 2 - 140, 0, w / 2 + 140, 0)
        sg.addColorStop(0, "#fbcfe8")
        sg.addColorStop(1, "#c4b5fd")
        ctx.fillStyle = sg
        ctx.fillText("Reach Beyond the Stars", w / 2, h * 0.56)
        ctx.font = "12px system-ui, sans-serif"
        ctx.fillStyle = "rgba(255,255,255,0.4)"
        ctx.fillText("点击画面或空格 · Restart", w / 2, h * 0.66)
      }

      rafRef.current = requestAnimationFrame(loop)
    }

    rafRef.current = requestAnimationFrame(loop)

    return () => {
      ro.disconnect()
      window.removeEventListener("keydown", onKeyDown)
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      rafRef.current = null
      lastTsRef.current = 0
    }
  }, [resizeCanvas, resetPlayingState, tryJump, trySlide, tryActivateBoost])

  const onCanvasPointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (rulesModalOpen) return
    const s = stateRef.current
    if (!s) return
    if (s.mode === "playing") s.touchStartY = e.clientY
    else s.touchStartY = null
    tryJump()
  }

  const onCanvasPointerUp = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const s = stateRef.current
    if (!s || s.touchStartY == null) return
    const dy = e.clientY - s.touchStartY
    s.touchStartY = null
    if (s.mode === "playing" && dy > 55) {
      s.slideEndAt = performance.now() / 1000 + SLIDE_DURATION_SEC
    }
  }

  return (
    <div className="relative flex h-full min-h-0 min-h-full flex-col bg-[#050508] text-white">
      <div className="relative z-20 flex shrink-0 items-center justify-between gap-3 border-b border-white/[0.08] px-4 py-3 backdrop-blur-xl">
        <button
          type="button"
          onClick={() => router.push("/lobby")}
          className="rounded-full border border-white/15 bg-white/[0.06] px-4 py-2 text-sm text-white/90 transition hover:bg-white/10 active:scale-[0.98]"
        >
          返回大厅
        </button>
        <span className="bg-gradient-to-r from-pink-200 via-fuchsia-200 to-violet-300 bg-clip-text text-sm font-semibold tracking-tight text-transparent">
          AsterNova · Star Dash
        </span>
        <span className="hidden max-w-[10rem] text-right text-[11px] leading-tight text-white/40 sm:block">
          Space 跳 · E 星爆 · ↓ 铲
        </span>
        <span className="w-14 sm:hidden" aria-hidden />
      </div>

      {rulesModalOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 p-4 backdrop-blur-md"
          role="dialog"
          aria-modal="true"
          aria-labelledby="star-dash-rules-title"
        >
          <div className="w-full max-w-[420px] rounded-[2rem] border border-white/[0.12] bg-white/[0.07] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.55)] backdrop-blur-2xl">
            <h2
              id="star-dash-rules-title"
              className="text-center text-xl font-semibold tracking-tight text-white"
              style={{ fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif" }}
            >
              怎么玩
            </h2>
            <p className="mt-1 text-center text-[13px] text-white/45">AsterNova · Star Dash · Let&apos;s Running</p>

            <ul className="mt-5 space-y-4 text-[14px] leading-relaxed text-white/80">
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <DashIconJump />
                <div>
                  <div className="font-medium text-white/95">跳跃 & 二段跳</div>
                  <div className="mt-0.5 text-[13px] text-white/55">点击画面、空格或左下「跳跃」；空中可再跳一次。</div>
                </div>
              </li>
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <DashIconSlide />
                <div>
                  <div className="font-medium text-white/95">滑铲</div>
                  <div className="mt-0.5 text-[13px] text-white/55">手指在画面上向下滑，或按 ↓ / 右下按钮。矮身钻过<span className="text-pink-200/90">悬空横梁</span>。</div>
                </div>
              </li>
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <DashIconStarBurst />
                <div>
                  <div className="font-medium text-white/95">星尘 & 加速</div>
                  <div className="mt-0.5 text-[13px] text-white/55">
                    收集星尘；满 10 颗后点中间<span className="text-amber-200/90">「星爆加速」</span>或按 E，进入短暂无敌加速并可撞碎障碍。
                  </div>
                </div>
              </li>
              <li className="flex gap-3 rounded-2xl bg-white/[0.05] p-3">
                <span className="flex h-11 w-11 shrink-0 flex-col items-center justify-center gap-0.5 rounded-2xl bg-gradient-to-br from-sky-300/30 to-pink-400/25 px-1 text-[10px] font-semibold leading-none text-white/90" aria-hidden>
                  <span>∞</span>
                  <span>盾</span>
                </span>
                <div>
                  <div className="font-medium text-white/95">道具（约每 20 秒）</div>
                  <div className="mt-0.5 text-[13px] text-white/55">
                    <span className="text-pink-200/85">磁吸</span>自动拉近星尘；<span className="text-sky-200/85">护盾</span>抵挡一次撞击。
                  </div>
                </div>
              </li>
            </ul>

            <label className="mt-5 flex cursor-pointer items-center gap-3 rounded-2xl border border-white/[0.08] bg-white/[0.04] px-4 py-3 text-[13px] text-white/70 transition hover:bg-white/[0.06]">
              <input
                type="checkbox"
                checked={dontShowRulesAgain}
                onChange={(e) => setDontShowRulesAgain(e.target.checked)}
                className="h-4 w-4 rounded-md border-white/30 bg-white/10 text-violet-500 focus:ring-violet-400/50"
              />
              下次不再显示规则（本机记住）
            </label>

            <button
              type="button"
              onClick={confirmRules}
              className="mt-5 w-full rounded-2xl bg-gradient-to-r from-pink-400/90 via-fuchsia-400/90 to-violet-500/90 py-3.5 text-[15px] font-semibold text-gray-950 shadow-lg shadow-fuchsia-500/20 transition hover:brightness-105 active:scale-[0.99]"
              style={{ fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif" }}
            >
              知道了
            </button>
          </div>
        </div>
      ) : null}

      <div className="relative flex min-h-0 flex-1 flex-col items-center justify-center px-3 pb-[max(1rem,env(safe-area-inset-bottom))] pt-3 min-[480px]:px-4">
        <div
          ref={wrapRef}
          className="relative mx-auto aspect-video h-full w-full max-w-[min(100%,960px)] max-h-[720px] min-h-[200px] overflow-hidden rounded-[1.75rem] border border-white/[0.1] shadow-[0_0_60px_rgba(168,85,247,0.12)]"
        >
          <canvas
            ref={canvasRef}
            onPointerDown={onCanvasPointerDown}
            onPointerUp={onCanvasPointerUp}
            className={`block h-full w-full cursor-pointer touch-none ${rulesModalOpen ? "pointer-events-none" : ""}`}
          />
          {screenMode === "playing" && !rulesModalOpen ? (
            <div className="pointer-events-auto absolute inset-x-0 bottom-0 z-30 flex items-end justify-between gap-2 px-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-12 sm:gap-3 sm:px-3">
              <button
                type="button"
                onPointerDown={(e) => {
                  e.preventDefault()
                  tryJump()
                }}
                className="flex h-[3.25rem] min-w-[5.5rem] shrink-0 items-center gap-2 rounded-2xl border border-pink-300/40 bg-gradient-to-b from-pink-400/35 to-violet-600/25 pl-1.5 pr-2.5 text-xs font-semibold text-white shadow-lg shadow-pink-500/15 backdrop-blur-md sm:h-14 sm:min-w-[6.25rem] sm:gap-2.5 sm:pl-2 sm:pr-3 sm:text-sm active:scale-95"
                style={{ touchAction: "manipulation" }}
              >
                <DashIconJump iconClass="h-9 w-9 sm:h-10 sm:w-10" />
                <span className="pr-0.5">跳跃</span>
              </button>
              <button
                type="button"
                onPointerDown={(e) => {
                  e.preventDefault()
                  tryActivateBoost()
                }}
                className={`flex h-[3.25rem] min-w-[6rem] shrink-0 items-center gap-1.5 rounded-2xl border pl-1.5 pr-2 text-[11px] font-bold leading-tight shadow-lg backdrop-blur-md sm:h-14 sm:min-w-[7rem] sm:gap-2 sm:pl-2 sm:pr-2.5 sm:text-xs active:scale-95 ${
                  boostReadyUi
                    ? "border-amber-300/50 bg-gradient-to-b from-amber-300/40 to-orange-500/30 text-amber-50 shadow-amber-500/25 animate-pulse"
                    : "border-white/10 bg-white/5 text-white/40"
                }`}
                style={{ touchAction: "manipulation" }}
              >
                <span className={boostReadyUi ? "" : "opacity-45"}>
                  <DashIconStarBurst iconClass="h-9 w-9 sm:h-10 sm:w-10" />
                </span>
                <span className="flex flex-col items-start font-semibold leading-tight">
                  <span>星爆</span>
                  <span className="text-[9px] font-normal opacity-90 sm:text-[10px]">加速</span>
                </span>
              </button>
              <button
                type="button"
                onPointerDown={(e) => {
                  e.preventDefault()
                  trySlide()
                }}
                className="flex h-[3.25rem] min-w-[5.5rem] shrink-0 items-center gap-2 rounded-2xl border border-violet-300/40 bg-gradient-to-b from-violet-400/35 to-fuchsia-600/25 pl-1.5 pr-2.5 text-xs font-semibold text-white shadow-lg shadow-violet-500/15 backdrop-blur-md sm:h-14 sm:min-w-[6.25rem] sm:gap-2.5 sm:pl-2 sm:pr-3 sm:text-sm active:scale-95"
                style={{ touchAction: "manipulation" }}
              >
                <DashIconSlide iconClass="h-9 w-9 sm:h-10 sm:w-10" />
                <span className="pr-0.5">滑铲</span>
              </button>
            </div>
          ) : null}
        </div>

        {isGameOver ? (
          <div className="mt-4 flex justify-center">
            <button
              type="button"
              onClick={() => {
                const s = stateRef.current
                if (s) resetPlayingState(s)
              }}
              className="rounded-full bg-gradient-to-r from-pink-300 via-fuchsia-300 to-violet-400 px-8 py-2.5 text-sm font-semibold text-gray-900 shadow-lg shadow-fuchsia-500/25 transition hover:brightness-105 active:scale-[0.98]"
            >
              Restart
            </button>
          </div>
        ) : null}
      </div>
      <LoopingBgmControl src="/audio/games/lets-running/Digital_Frenzy lets running.mp3" storageKey="bgm-volume:lets-running" />
    </div>
  )
}
