"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import Matter, {
  Body,
  Bodies,
  Composite,
  Constraint,
  Engine,
  Events,
  Render,
  Runner,
  World,
} from "matter-js"

import { LoopingBgmControl } from "@/src/components/audio/LoopingBgmControl"
import styles from "./GameEngine.module.css"

const WIDTH = 1180
const HEIGHT = 700
const LAUNCH_X = 170
const LAUNCH_Y = HEIGHT - 145
const BALL_RADIUS = 18
/** 拖拽向量 → 初速度倍率（越大越有劲） */
const LAUNCH_VELOCITY_SCALE = 0.33
/** 撞到晶体并消除时，对小球速度乘以此系数（阻尼减速，连锁爆炸补足清场） */
const HIT_VELOCITY_DAMP = 0.86
/** 方块被消除时，此半径内的其他晶体会连锁爆炸（世界坐标像素） */
const CHAIN_BLAST_RADIUS = 82
/** 发射后连续这么久未碰到晶体则强制收球并结算（毫秒） */
const BALL_NO_CRYSTAL_MS = 5000
const STORAGE_SKIP_RULES = "shoot-them-all-skip-rules"

type DestroyableBody = Matter.Body & { render: Matter.IBodyRenderOptions }
type Phase = "aiming" | "flying" | "resolving" | "game-over"
type RoundOutcome = "pass" | "fail"

function randomInt(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

function RulesIconAim() {
  return (
    <span className={`${styles.rulesIcon} ${styles.rulesIconAim}`} aria-hidden>
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M7 17 L17 7 M17 7 h-4.5 M17 7 v4.5" opacity={0.85} />
        <circle cx="9" cy="15" r="2.2" />
      </svg>
    </span>
  )
}

function RulesIconTarget() {
  return (
    <span className={`${styles.rulesIcon} ${styles.rulesIconTarget}`} aria-hidden>
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.45" strokeLinecap="round">
        <circle cx="12" cy="12" r="7" />
        <circle cx="12" cy="12" r="3.2" />
        <path d="M12 5v2 M12 17v2 M5 12h2 M17 12h2" />
      </svg>
    </span>
  )
}

function RulesIconAmmo() {
  return (
    <span className={`${styles.rulesIcon} ${styles.rulesIconAmmo}`} aria-hidden>
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.45" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="9" cy="12" r="3.2" />
        <circle cx="15" cy="12" r="3.2" />
        <path d="M12 8v-2 M12 18v-2" />
      </svg>
    </span>
  )
}

function RulesIconTimer() {
  return (
    <span className={`${styles.rulesIcon} ${styles.rulesIconTimer}`} aria-hidden>
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.45" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="13" r="7" />
        <path d="M12 9.5V13l3 2" />
      </svg>
    </span>
  )
}

export function GameEngine() {
  const router = useRouter()
  const worldRef = React.useRef<HTMLDivElement | null>(null)

  const engineRef = React.useRef<Matter.Engine | null>(null)
  const renderRef = React.useRef<Matter.Render | null>(null)
  const runnerRef = React.useRef<Matter.Runner | null>(null)
  const elasticRef = React.useRef<Matter.Constraint | null>(null)
  const currentBallRef = React.useRef<Matter.Body | null>(null)
  const isDraggingRef = React.useRef(false)
  const dragPointRef = React.useRef<{ x: number; y: number } | null>(null)
  const pendingOutcomeRef = React.useRef<RoundOutcome | null>(null)
  const calmSinceRef = React.useRef<number>(0)
  const lastStopAtRef = React.useRef<number>(0)
  const settledRef = React.useRef<boolean>(false)
  const roundResolvedRef = React.useRef<boolean>(false)
  const totalObstaclesRef = React.useRef<number>(0)
  const destroyedObstaclesRef = React.useRef<number>(0)
  const obstacleIdsRef = React.useRef<Set<number>>(new Set())
  const ammoPoolRef = React.useRef<number>(1)
  const levelRef = React.useRef<number>(1)
  const scoreRef = React.useRef<number>(0)
  const phaseRef = React.useRef<Phase>("aiming")
  /** 当前飞行球最后一次碰到晶体的时间（发射时初始化为此时刻，用于超时收球） */
  const lastCrystalHitAtRef = React.useRef<number>(0)

  const [score, setScore] = React.useState(0)
  const [ammoPool, setAmmoPool] = React.useState(1)
  const [currentLevel, setCurrentLevel] = React.useState(1)
  const [clearanceRate, setClearanceRate] = React.useState(0)
  const [phase, setPhase] = React.useState<Phase>("aiming")
  const [gameOverStats, setGameOverStats] = React.useState<{ levels: number; score: number } | null>(null)
  const [rulesModalOpen, setRulesModalOpen] = React.useState(true)
  const [dontShowRulesAgain, setDontShowRulesAgain] = React.useState(false)
  const [fatalRuntimeError, setFatalRuntimeError] = React.useState<Error | null>(null)

  const syncPhase = React.useCallback((next: Phase) => {
    phaseRef.current = next
    setPhase(next)
  }, [])

  const syncScore = React.useCallback((next: number) => {
    scoreRef.current = next
    setScore(next)
  }, [])

  const syncAmmoPool = React.useCallback((next: number) => {
    ammoPoolRef.current = next
    setAmmoPool(next)
  }, [])

  const syncLevel = React.useCallback((next: number) => {
    levelRef.current = next
    setCurrentLevel(next)
  }, [])

  const updateClearance = React.useCallback(() => {
    const total = Math.max(1, totalObstaclesRef.current)
    const rate = Math.min(1, destroyedObstaclesRef.current / total)
    setClearanceRate(rate)
    return rate
  }, [])

  const clearRoundBodies = React.useCallback(() => {
    const engine = engineRef.current
    if (!engine) return
    const world = engine.world
    const allBodies = Composite.allBodies(world)
    for (const body of allBodies) {
      if (body.label === "nova-ball" || body.label === "crystal-block") {
        World.remove(world, body)
      }
    }
    if (elasticRef.current) {
      World.remove(world, elasticRef.current)
      elasticRef.current = null
    }
    currentBallRef.current = null
    pendingOutcomeRef.current = null
    calmSinceRef.current = 0
    settledRef.current = false
    obstacleIdsRef.current.clear()
  }, [])

  const addObstacle = React.useCallback((x: number, y: number, w: number, h: number) => {
    const body = Bodies.rectangle(x, y, w, h, {
      label: "crystal-block",
      friction: 0,
      frictionStatic: 0,
      restitution: 0.98,
      density: 0.0021,
      chamfer: { radius: 5 },
      render: {
        fillStyle: "rgba(180, 210, 255, 0.18)",
        strokeStyle: "rgba(178, 132, 255, 0.7)",
        lineWidth: 1.6,
      },
    }) as DestroyableBody
    obstacleIdsRef.current.add(body.id)
    totalObstaclesRef.current += 1
    World.add(engineRef.current!.world, body)
  }, [])

  const generateObstacleField = React.useCallback(() => {
    totalObstaclesRef.current = 0
    destroyedObstaclesRef.current = 0
    setClearanceRate(0)

    const groups = randomInt(3, 5)
    const startX = 760
    const span = 340

    for (let g = 0; g < groups; g++) {
      const groupX = startX + Math.floor((g / Math.max(1, groups - 1)) * span) + randomInt(-24, 24)
      const baseY = HEIGHT - 90
      const pattern = randomInt(0, 2)

      if (pattern === 0) {
        const columns = randomInt(2, 3)
        for (let c = 0; c < columns; c++) {
          const x = groupX + c * 52
          addObstacle(x, baseY - 34, 26, 74)
          addObstacle(x, baseY - 112, 26, 74)
        }
        addObstacle(groupX + 26, baseY - 155, 116, 20)
      } else if (pattern === 1) {
        addObstacle(groupX, baseY - 30, 104, 22)
        addObstacle(groupX + 60, baseY - 64, 104, 22)
        addObstacle(groupX + 14, baseY - 98, 104, 22)
        addObstacle(groupX + 84, baseY - 128, 84, 20)
      } else {
        addObstacle(groupX, baseY - 34, 24, 70)
        addObstacle(groupX + 44, baseY - 34, 24, 70)
        addObstacle(groupX + 22, baseY - 86, 96, 20)
        addObstacle(groupX + 22, baseY - 118, 56, 20)
      }
    }
  }, [addObstacle])

  const createBall = React.useCallback(() => {
    const engine = engineRef.current
    if (!engine || ammoPoolRef.current <= 0 || phaseRef.current === "game-over") return

    const ball = Bodies.circle(LAUNCH_X, LAUNCH_Y, BALL_RADIUS, {
      label: "nova-ball",
      restitution: 0.98,
      friction: 0,
      frictionStatic: 0,
      frictionAir: 0.001,
      density: 0.0032,
      render: {
        fillStyle: "rgba(255, 174, 226, 0.9)",
        strokeStyle: "rgba(255,255,255,0.9)",
        lineWidth: 1.2,
      },
    })

    const elastic = Constraint.create({
      pointA: { x: LAUNCH_X, y: LAUNCH_Y },
      bodyB: ball,
      stiffness: 0.045,
      damping: 0.02,
      length: 0,
      render: {
        visible: true,
        strokeStyle: "rgba(255, 205, 235, 0.55)",
        lineWidth: 2,
      },
    })

    World.add(engine.world, [ball, elastic])
    currentBallRef.current = ball
    elasticRef.current = elastic
    settledRef.current = false
    lastStopAtRef.current = 0
    syncPhase("aiming")
  }, [syncPhase])

  const resolveRound = React.useCallback(
    (passed: boolean) => {
      if (roundResolvedRef.current || phaseRef.current === "game-over") return
      roundResolvedRef.current = true
      syncPhase("resolving")
      calmSinceRef.current = 0

      const nextLevel = levelRef.current + 1
      const ammoNow = ammoPoolRef.current
      const nextAmmo = passed ? ammoNow + 1 : ammoNow - 1
      const levelSnapshot = levelRef.current

      window.setTimeout(() => {
        pendingOutcomeRef.current = null
        if (!passed && nextAmmo <= 0) {
          syncPhase("game-over")
          setGameOverStats({
            levels: Math.max(0, levelSnapshot - 1),
            score: scoreRef.current,
          })
          return
        }

        syncAmmoPool(Math.max(0, nextAmmo))
        syncLevel(nextLevel)
        clearRoundBodies()
        generateObstacleField()
        if (ammoPoolRef.current > 0) {
          createBall()
        }
        roundResolvedRef.current = false
      }, passed ? 880 : 980)
    },
    [clearRoundBodies, createBall, generateObstacleField, syncAmmoPool, syncLevel, syncPhase],
  )

  const destroyObstacle = React.useCallback(
    (body: Matter.Body) => {
      if (!obstacleIdsRef.current.has(body.id)) return
      const engine = engineRef.current
      if (!engine) return

      const cx = body.position.x
      const cy = body.position.y
      const r2 = CHAIN_BLAST_RADIUS * CHAIN_BLAST_RADIUS

      obstacleIdsRef.current.delete(body.id)
      destroyedObstaclesRef.current += 1
      World.remove(engine.world, body)
      syncScore(scoreRef.current + 120)
      const rate = updateClearance()
      if (rate >= 0.6 && !pendingOutcomeRef.current) {
        pendingOutcomeRef.current = "pass"
        calmSinceRef.current = 0
        syncPhase("resolving")
      }

      const neighbors: Matter.Body[] = []
      for (const b of Composite.allBodies(engine.world)) {
        if (b.label !== "crystal-block" || !obstacleIdsRef.current.has(b.id)) continue
        const dx = b.position.x - cx
        const dy = b.position.y - cy
        if (dx * dx + dy * dy <= r2) {
          neighbors.push(b)
        }
      }
      for (const n of neighbors) {
        destroyObstacle(n)
      }
    },
    [syncPhase, syncScore, updateClearance],
  )

  const maybeSpawnNextBallOrFail = React.useCallback(() => {
    if (phaseRef.current === "game-over" || roundResolvedRef.current) return
    const rate = Math.min(1, destroyedObstaclesRef.current / Math.max(1, totalObstaclesRef.current))
    if (pendingOutcomeRef.current === "pass" || rate >= 0.6) return

    if (ammoPoolRef.current > 0) {
      createBall()
      return
    }

    if (!pendingOutcomeRef.current) {
      pendingOutcomeRef.current = "fail"
      calmSinceRef.current = 0
      syncPhase("resolving")
    }
  }, [createBall, syncPhase])

  const clampDragPoint = React.useCallback((x: number, y: number) => {
    const dx = x - LAUNCH_X
    const dy = y - LAUNCH_Y
    const maxPull = 140
    const dist = Math.hypot(dx, dy)
    if (dist <= maxPull) return { x, y }
    const ratio = maxPull / Math.max(1, dist)
    return { x: LAUNCH_X + dx * ratio, y: LAUNCH_Y + dy * ratio }
  }, [])

  const getWorldPoint = React.useCallback((clientX: number, clientY: number) => {
    const render = renderRef.current
    if (!render) return null
    const rect = render.canvas.getBoundingClientRect()
    const sx = WIDTH / rect.width
    const sy = HEIGHT / rect.height
    return {
      x: (clientX - rect.left) * sx,
      y: (clientY - rect.top) * sy,
    }
  }, [])

  const launchIfDragging = React.useCallback(() => {
    if (!isDraggingRef.current) return
    isDraggingRef.current = false

    const ball = currentBallRef.current
    const engine = engineRef.current
    if (!ball || !engine) return

    const elastic = elasticRef.current
    if (elastic) {
      World.remove(engine.world, elastic)
      elasticRef.current = null
    }
    dragPointRef.current = null

    const pullX = LAUNCH_X - ball.position.x
    const pullY = LAUNCH_Y - ball.position.y
    const pullLen = Math.hypot(pullX, pullY)
    if (pullLen < 8) {
      Body.setStatic(ball, false)
      Body.setPosition(ball, { x: LAUNCH_X, y: LAUNCH_Y })
      Body.setVelocity(ball, { x: 0, y: 0 })
      Body.setAngularVelocity(ball, 0)
      const newElastic = Constraint.create({
        pointA: { x: LAUNCH_X, y: LAUNCH_Y },
        bodyB: ball,
        stiffness: 0.045,
        damping: 0.02,
        length: 0,
        render: {
          visible: true,
          strokeStyle: "rgba(255, 205, 235, 0.55)",
          lineWidth: 2,
        },
      })
      World.add(engine.world, newElastic)
      elasticRef.current = newElastic
      syncPhase("aiming")
      return
    }

    Body.setStatic(ball, false)
    Body.setVelocity(ball, { x: pullX * LAUNCH_VELOCITY_SCALE, y: pullY * LAUNCH_VELOCITY_SCALE })
    Body.setAngularVelocity(ball, 0)
    settledRef.current = false
    lastStopAtRef.current = 0
    lastCrystalHitAtRef.current = Date.now()
    syncPhase("flying")
    const nextAmmo = Math.max(0, ammoPoolRef.current - 1)
    syncAmmoPool(nextAmmo)
  }, [syncAmmoPool, syncPhase])

  const engineCallbacksRef = React.useRef<{
    destroyObstacle: (body: Matter.Body) => void
    maybeSpawnNextBallOrFail: () => void
    resolveRound: (passed: boolean) => void
  }>({
    destroyObstacle: () => {},
    maybeSpawnNextBallOrFail: () => {},
    resolveRound: () => {},
  })
  engineCallbacksRef.current = {
    destroyObstacle,
    maybeSpawnNextBallOrFail,
    resolveRound,
  }

  React.useEffect(() => {
    if (!worldRef.current) return
    try {
      const engine = Engine.create({ gravity: { x: 0, y: 1.02 } })
      engineRef.current = engine

      const render = Render.create({
        element: worldRef.current,
        engine,
        options: {
          width: WIDTH,
          height: HEIGHT,
          wireframes: false,
          background: "transparent",
          pixelRatio: window.devicePixelRatio || 1,
        },
      })
      renderRef.current = render
      render.canvas.style.width = "100%"
      render.canvas.style.height = "100%"
      render.canvas.style.display = "block"

      const runner = Runner.create()
      runnerRef.current = runner

    const boundaries = [
      Bodies.rectangle(WIDTH / 2, HEIGHT + 40, WIDTH + 120, 80, {
        isStatic: true,
        label: "floor",
        friction: 0.06,
        frictionStatic: 0.06,
        restitution: 0.72,
        render: { visible: false },
      }),
      Bodies.rectangle(-40, HEIGHT / 2, 80, HEIGHT + 120, {
        isStatic: true,
        label: "left-wall",
        friction: 0,
        restitution: 0.9,
        render: { visible: false },
      }),
      Bodies.rectangle(WIDTH + 40, HEIGHT / 2, 80, HEIGHT + 120, {
        isStatic: true,
        label: "right-wall",
        friction: 0,
        restitution: 0.9,
        render: { visible: false },
      }),
      Bodies.rectangle(WIDTH / 2, -40, WIDTH + 120, 80, {
        isStatic: true,
        label: "ceiling",
        friction: 0,
        restitution: 0.85,
        render: { visible: false },
      }),
      Bodies.rectangle(330, HEIGHT - 34, 240, 20, {
        isStatic: true,
        angle: -0.06,
        label: "launch-ramp",
        friction: 0,
        frictionStatic: 0,
        restitution: 0.95,
        render: { fillStyle: "rgba(70, 84, 126, 0.35)" },
      }),
    ]
    World.add(engine.world, boundaries)

    Events.on(engine, "collisionStart", (event) => {
      for (const pair of event.pairs) {
        const a = pair.bodyA
        const b = pair.bodyB
        const hitObstacle = a.label === "crystal-block" || b.label === "crystal-block"
        const hitBall = a.label === "nova-ball" || b.label === "nova-ball"
        if (!hitObstacle || !hitBall) continue

        const ball = a.label === "nova-ball" ? a : b
        const obstacle = a.label === "crystal-block" ? a : b

        if (currentBallRef.current?.id === ball.id) {
          lastCrystalHitAtRef.current = Date.now()
        }

        const vx = ball.velocity.x
        const vy = ball.velocity.y
        Body.setVelocity(ball, { x: vx * HIT_VELOCITY_DAMP, y: vy * HIT_VELOCITY_DAMP })

        engineCallbacksRef.current.destroyObstacle(obstacle)
      }
    })

    Events.on(engine, "afterUpdate", () => {
      const ball = currentBallRef.current
      if (phaseRef.current === "game-over" || roundResolvedRef.current) return

      if (pendingOutcomeRef.current) {
        const totalObs = totalObstaclesRef.current
        const destroyedObs = destroyedObstaclesRef.current
        if (
          pendingOutcomeRef.current === "pass" &&
          totalObs > 0 &&
          destroyedObs >= totalObs
        ) {
          engineCallbacksRef.current.resolveRound(true)
          return
        }

        const movingBodies = Composite.allBodies(engine.world).filter(
          (body) =>
            !body.isStatic &&
            (body.label === "crystal-block" || body.label === "nova-ball") &&
            Math.hypot(body.velocity.x, body.velocity.y) > 0.18,
        )

        if (movingBodies.length === 0) {
          if (!calmSinceRef.current) {
            calmSinceRef.current = Date.now()
          } else if (Date.now() - calmSinceRef.current > 760) {
            engineCallbacksRef.current.resolveRound(pendingOutcomeRef.current === "pass")
            return
          }
        } else {
          calmSinceRef.current = 0
        }
      }

      if (!ball) return
      if (isDraggingRef.current) return
      // 已标记过关/失败、等全场静止再 resolve 时，不要走收球逻辑，否则会误删球并打断结算
      if (pendingOutcomeRef.current != null) return

      const speed = ball.speed
      const outOfBounds = ball.position.x > WIDTH + 120 || ball.position.x < -120 || ball.position.y > HEIGHT + 120
      if (outOfBounds) {
        World.remove(engine.world, ball)
        currentBallRef.current = null
        engineCallbacksRef.current.maybeSpawnNextBallOrFail()
        return
      }

      if (elasticRef.current) return

      if (phaseRef.current === "flying" && Date.now() - lastCrystalHitAtRef.current >= BALL_NO_CRYSTAL_MS) {
        World.remove(engine.world, ball)
        currentBallRef.current = null
        settledRef.current = false
        lastStopAtRef.current = 0
        engineCallbacksRef.current.maybeSpawnNextBallOrFail()
        return
      }

      if (speed < 0.22) {
        if (!lastStopAtRef.current) {
          lastStopAtRef.current = Date.now()
        } else if (Date.now() - lastStopAtRef.current > 900) {
          settledRef.current = true
        }
      } else {
        lastStopAtRef.current = 0
      }

      if (settledRef.current) {
        World.remove(engine.world, ball)
        currentBallRef.current = null
        settledRef.current = false
        lastStopAtRef.current = 0
        engineCallbacksRef.current.maybeSpawnNextBallOrFail()
      }
    })

    Events.on(render, "afterRender", () => {
      const ctx = render.context

      // Launch anchor
      ctx.save()
      ctx.beginPath()
      ctx.arc(LAUNCH_X, LAUNCH_Y, 8, 0, Math.PI * 2)
      ctx.fillStyle = "rgba(255, 210, 240, 0.9)"
      ctx.shadowColor = "rgba(232, 155, 255, 0.75)"
      ctx.shadowBlur = 14
      ctx.fill()
      ctx.restore()

      // Predicted trajectory while aiming
      const ball = currentBallRef.current
      if (ball && isDraggingRef.current) {
        const vx = (LAUNCH_X - ball.position.x) * LAUNCH_VELOCITY_SCALE
        const vy = (LAUNCH_Y - ball.position.y) * LAUNCH_VELOCITY_SCALE
        ctx.save()
        for (let i = 1; i <= 22; i++) {
          const t = i * 0.11
          const px = LAUNCH_X + vx * t * 8
          const py = LAUNCH_Y + vy * t * 8 + 0.5 * engine.gravity.y * Math.pow(t * 8, 2) * 0.06
          const alpha = Math.max(0, 0.5 - i * 0.02)
          ctx.beginPath()
          ctx.arc(px, py, 2.2, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(255, 213, 236, ${alpha})`
          ctx.fill()
        }
        ctx.restore()
      }

      if (ball && (elasticRef.current || isDraggingRef.current)) {
        ctx.save()
        ctx.beginPath()
        ctx.moveTo(LAUNCH_X, LAUNCH_Y)
        ctx.lineTo(ball.position.x, ball.position.y)
        ctx.strokeStyle = "rgba(255,205,235,0.55)"
        ctx.lineWidth = 2
        ctx.stroke()
        ctx.restore()
      }

      // Nova ball glow pass
      if (ball) {
        ctx.save()
        const gradient = ctx.createRadialGradient(
          ball.position.x - BALL_RADIUS * 0.3,
          ball.position.y - BALL_RADIUS * 0.4,
          2,
          ball.position.x,
          ball.position.y,
          BALL_RADIUS * 1.45,
        )
        gradient.addColorStop(0, "rgba(255, 235, 246, 0.98)")
        gradient.addColorStop(0.35, "rgba(255, 186, 232, 0.95)")
        gradient.addColorStop(0.7, "rgba(207, 138, 255, 0.9)")
        gradient.addColorStop(1, "rgba(136, 92, 246, 0.86)")
        ctx.beginPath()
        ctx.arc(ball.position.x, ball.position.y, BALL_RADIUS, 0, Math.PI * 2)
        ctx.fillStyle = gradient
        ctx.shadowColor = "rgba(223, 128, 255, 0.85)"
        ctx.shadowBlur = 18
        ctx.fill()
        ctx.restore()
      }
    })

      Render.run(render)
      Runner.run(runner, engine)

    clearRoundBodies()
    syncScore(0)
    syncAmmoPool(1)
    syncLevel(1)
    roundResolvedRef.current = false
    pendingOutcomeRef.current = null
    calmSinceRef.current = 0
    setGameOverStats(null)
    generateObstacleField()
    createBall()

      return () => {
        Render.stop(render)
        Runner.stop(runner)
        Composite.clear(engine.world, false)
        Engine.clear(engine)
        if (render.canvas.parentNode) {
          render.canvas.parentNode.removeChild(render.canvas)
        }
        // Clear texture cache for hot reload safety
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ;(render as any).textures = {}
      }
    }
    catch (err) {
      setFatalRuntimeError(err instanceof Error ? err : new Error(String(err)))
      return
    }
    // 仅挂载时创建引擎。若依赖 clearanceRate 等会变的回调，effect 会反复 teardown，
    // 导致 syncLevel(1) 再次执行，表现为「打一枪就回到第一关」。
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const progressPercent = Math.round(clearanceRate * 100)
  const passed = clearanceRate >= 0.6
  const ammoIconCount = Math.min(ammoPool, 12)

  React.useEffect(() => {
    const onWindowPointerUp = () => launchIfDragging()
    window.addEventListener("pointerup", onWindowPointerUp)
    return () => window.removeEventListener("pointerup", onWindowPointerUp)
  }, [launchIfDragging])

  React.useLayoutEffect(() => {
    try {
      if (localStorage.getItem(STORAGE_SKIP_RULES) === "1") setRulesModalOpen(false)
    } catch {
      /* ignore */
    }
  }, [])

  const confirmRules = React.useCallback(() => {
    try {
      if (dontShowRulesAgain) localStorage.setItem(STORAGE_SKIP_RULES, "1")
    } catch {
      /* ignore */
    }
    setRulesModalOpen(false)
  }, [dontShowRulesAgain])

  const handleRestart = () => {
    if (!engineRef.current) return
    roundResolvedRef.current = false
    pendingOutcomeRef.current = null
    calmSinceRef.current = 0
    isDraggingRef.current = false
    dragPointRef.current = null
    setGameOverStats(null)
    syncPhase("aiming")
    clearRoundBodies()
    syncScore(0)
    syncAmmoPool(1)
    syncLevel(1)
    setClearanceRate(0)
    generateObstacleField()
    createBall()
  }

  if (fatalRuntimeError) {
    return (
      <div className={styles.shell}>
        <div className={styles.overlay}>
          <div className={styles.panel}>
            <div className={styles.panelTitle}>游戏初始化失败</div>
            <div className={styles.panelLine} style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
              {fatalRuntimeError.message}
            </div>
            <div className={styles.panelLine} style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", fontSize: 12, opacity: 0.85 }}>
              {fatalRuntimeError.stack || "(no stack trace)"}
            </div>
            <div className={styles.panelActions}>
              <button type="button" className={`${styles.actionBtn} ${styles.actionPrimary}`} onClick={() => router.refresh()}>
                重试
              </button>
              <button type="button" className={`${styles.actionBtn} ${styles.actionSecondary}`} onClick={() => router.push("/lobby")}>
                返回大厅
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.shell}>
      <div className={styles.stars} />

      {rulesModalOpen ? (
        <div className={styles.rulesBackdrop} role="dialog" aria-modal="true" aria-labelledby="sta-rules-title">
          <div className={styles.rulesPanel}>
            <h2 id="sta-rules-title" className={styles.rulesTitle}>
              规则速览
            </h2>
            <p className={styles.rulesSubtitle}>Shoot Them All · 物理弹射清场</p>

            <ul className={styles.rulesList}>
              <li className={styles.rulesRow}>
                <RulesIconAim />
                <div>
                  <div className={styles.rulesRowTitle}>拖拽发射</div>
                  <p className={styles.rulesRowDesc}>按住左侧 Nova 球向后拉，松手弹出；连锁爆炸可顺带清掉邻近晶体。</p>
                </div>
              </li>
              <li className={styles.rulesRow}>
                <RulesIconTarget />
                <div>
                  <div className={styles.rulesRowTitle}>过关线 60%</div>
                  <p className={styles.rulesRowDesc}>本关消除晶体达到 60% 即算过关；全清会更快进入结算。</p>
                </div>
              </li>
              <li className={styles.rulesRow}>
                <RulesIconAmmo />
                <div>
                  <div className={styles.rulesRowTitle}>全局球数</div>
                  <p className={styles.rulesRowDesc}>
                    每发射 1 次消耗 1 球。<span className={styles.rulesEmphPass}>过关 +1</span>，{" "}
                    <span className={styles.rulesEmphFail}>未达标 −1</span>。未达标且扣完后球数 ≤0 时游戏结束。
                  </p>
                </div>
              </li>
              <li className={styles.rulesRow}>
                <RulesIconTimer />
                <div>
                  <div className={styles.rulesRowTitle}>5 秒未碰晶体</div>
                  <p className={styles.rulesRowDesc}>单颗球若连续 5 秒没撞到晶体，会自动收回并计作一次出手结束。</p>
                </div>
              </li>
            </ul>

            <label className={styles.rulesCheck}>
              <input
                type="checkbox"
                checked={dontShowRulesAgain}
                onChange={(e) => setDontShowRulesAgain(e.target.checked)}
              />
              下次不再显示（仅本机）
            </label>

            <button type="button" className={styles.rulesConfirm} onClick={confirmRules}>
              开始游戏
            </button>
          </div>
        </div>
      ) : null}

      <div className={styles.hud}>
        <div className={styles.topRow}>
          <div className={styles.title}>Shoot Them All</div>
          <div className={styles.pillRow}>
            <span className={styles.pill}>第 {currentLevel} 关</span>
            <span className={`${styles.pill} ${styles.ammoPill}`} title={`全局剩余球：${ammoPool}`}>
              <span className={styles.ammoPillMain}>
                <span>全局剩余球</span>
                <span className={styles.ammoNumber}>{ammoPool}</span>
              </span>
              <span className={styles.ballIcons} aria-hidden>
                {Array.from({ length: ammoIconCount }).map((_, idx) => (
                  <span key={`ammo-${idx}`} className={styles.ballDot} />
                ))}
                {ammoPool > 12 ? <span className={styles.ballCountText}>+{ammoPool - 12}</span> : null}
              </span>
            </span>
            <span className={styles.pill}>得分 {score}</span>
            <button className={styles.backBtn} onClick={() => router.push("/lobby")} type="button">
              返回大厅
            </button>
          </div>
        </div>

        <div className={styles.progressWrap}>
          <div className={styles.progressLabel}>
            <span>晶体清除目标：60%</span>
            <span>{progressPercent}%</span>
          </div>
          <div className={styles.progressTrack}>
            <div className={`${styles.progressFill} ${passed ? styles.progressFillSuccess : ""}`} style={{ width: `${progressPercent}%` }} />
          </div>
        </div>
      </div>

      <div
        className={`${styles.canvasWrap} ${rulesModalOpen ? styles.canvasBlocked : ""}`}
        ref={worldRef}
        onPointerDown={(ev) => {
          const ball = currentBallRef.current
          const engine = engineRef.current
          if (!ball || !engine || phaseRef.current !== "aiming") return
          const point = getWorldPoint(ev.clientX, ev.clientY)
          if (!point) return

          const dist = Math.hypot(point.x - ball.position.x, point.y - ball.position.y)
          if (dist > BALL_RADIUS * 2.4) return

          const existingElastic = elasticRef.current
          if (existingElastic) {
            World.remove(engine.world, existingElastic)
            elasticRef.current = null
          }

          isDraggingRef.current = true
          const clamped = clampDragPoint(point.x, point.y)
          dragPointRef.current = clamped
          Body.setStatic(ball, true)
          Body.setPosition(ball, clamped)
          Body.setVelocity(ball, { x: 0, y: 0 })
          Body.setAngularVelocity(ball, 0)
        }}
        onPointerMove={(ev) => {
          if (!isDraggingRef.current) return
          const ball = currentBallRef.current
          if (!ball) return
          const point = getWorldPoint(ev.clientX, ev.clientY)
          if (!point) return
          const clamped = clampDragPoint(point.x, point.y)
          dragPointRef.current = clamped
          Body.setPosition(ball, clamped)
        }}
        onPointerUp={launchIfDragging}
      >
        <div className={styles.hint}>拖拽左侧 Nova 发射；过关 +1 球，未达标 −1 球（详见开始前的规则）。</div>

        {phase === "game-over" && gameOverStats ? (
          <div className={styles.overlay}>
            <div className={styles.panel}>
              <div className={styles.panelTitle}>游戏结束</div>
              <div className={styles.panelLine}>生存关数：{gameOverStats.levels}</div>
              <div className={styles.panelLine}>总得分：{gameOverStats.score}</div>
              <div className={styles.panelSlogan}>Reach Beyond the Stars</div>
              <div className={styles.panelActions}>
                <button type="button" className={`${styles.actionBtn} ${styles.actionPrimary}`} onClick={handleRestart}>
                  重新开始
                </button>
                <button type="button" className={`${styles.actionBtn} ${styles.actionSecondary}`} onClick={() => router.push("/lobby")}>
                  返回大厅
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </div>
      <LoopingBgmControl src="/audio/games/shoot-them-all/Untitled.mp3" storageKey="bgm-volume:shoot-them-all" />
    </div>
  )
}

