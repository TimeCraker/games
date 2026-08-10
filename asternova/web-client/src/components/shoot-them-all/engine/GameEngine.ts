import Matter from "matter-js"

import { HEIGHT, PHYS, WIDTH } from "../constants"
import { generateCrystalCluster } from "./content/pegLayouts"
import { Entity, EntityRegistry } from "./EntityRegistry"
import { GhostPredictor, TrajectoryResult } from "./GhostPredictor"
import { PhysicsWorld } from "./PhysicsWorld"

export type StaPhase = "aiming" | "flying" | "resolving" | "game-over"

/** 引擎事件（引擎层零 Pixi；渲染层订阅以触发粒子/屏震/音效）。 */
export type EngineEvent =
  | { type: "launch" }
  | { type: "peg-broken"; x: number; y: number; kind: string }
  | { type: "node-clear"; x: number; y: number }

/** 75% 清除即过关（Stage Spec §3.8 晶体节点）。 */
const NODE_CLEAR_RATIO = 0.75
/** 清空后停留庆祝再进入下一簇（毫秒）。 */
const RESOLVE_MS = 1100

/**
 * 纯 TS 游戏引擎（Stage Spec §8.1/§8.11）。零 React/Pixi 依赖。
 *
 * M1 范围：发射器瞄准/发射、标准陨星物理、晶体钉碰撞破碎、轨迹预测、
 * 75% 清空过关循环（aiming→flying→resolving→aiming）、事件回调驱动 Juice。
 */
export class GameEngine {
  readonly physics = new PhysicsWorld()
  readonly registry = new EntityRegistry()

  phase: StaPhase = "aiming"
  aimAngle = 0
  score = 0
  /** 供渲染层订阅的事件回调。 */
  onEvent: ((e: EngineEvent) => void) | null = null

  private ball: Entity | null = null
  private ballStopSince = 0
  private predictor: GhostPredictor
  private pegsTotal = 0
  private nodeCleared = false
  private resolvingTimer = 0

  constructor() {
    this.setupCollisions()
    this.spawnPegs()
    this.spawnBall()
    this.predictor = new GhostPredictor(this.registry)
  }

  get ballEntity(): Entity | null {
    return this.ball
  }

  predictTrajectory(): TrajectoryResult {
    if (this.phase !== "aiming") return { points: [], firstHit: -1 }
    return this.predictor.predict(this.aimAngle)
  }

  setAimFromPoint(px: number, py: number): void {
    if (this.phase !== "aiming") return
    const dx = px - PHYS.launchAnchor.x
    const dy = Math.max(1, py - PHYS.launchAnchor.y)
    const theta = Math.atan2(dx, dy)
    this.aimAngle = Math.max(-PHYS.angleMax, Math.min(PHYS.angleMax, theta))
  }

  launch(): void {
    if (this.phase !== "aiming" || !this.ball) return
    const v = PHYS.v0
    Matter.Body.setStatic(this.ball.body, false)
    Matter.Body.setVelocity(this.ball.body, {
      x: Math.sin(this.aimAngle) * v,
      y: Math.cos(this.aimAngle) * v,
    })
    Matter.Body.setAngularVelocity(this.ball.body, 0)
    this.phase = "flying"
    this.ballStopSince = 0
    this.onEvent?.({ type: "launch" })
  }

  update(dtMs: number): void {
    this.physics.step(dtMs)

    if (this.phase === "flying" && this.ball) {
      this.tickFlying(dtMs)
    } else if (this.phase === "resolving") {
      this.resolvingTimer -= dtMs
      if (this.resolvingTimer <= 0) this.completeNode()
    }
  }

  private tickFlying(dtMs: number): void {
    const b = this.ball!.body
    const sp = Math.hypot(b.velocity.x, b.velocity.y)
    if (sp > PHYS.vMax) {
      const k = PHYS.vMax / sp
      Matter.Body.setVelocity(b, { x: b.velocity.x * k, y: b.velocity.y * k })
    }

    const out = b.position.y > HEIGHT + 120 || b.position.x < -120 || b.position.x > WIDTH + 120
    if (out) {
      this.respawnBall()
      return
    }
    if (sp < 0.3) {
      this.ballStopSince += dtMs
      if (this.ballStopSince > 600) this.respawnBall()
    } else {
      this.ballStopSince = 0
    }
  }

  private respawnBall(): void {
    if (!this.ball) return
    Matter.Body.setStatic(this.ball.body, true)
    Matter.Body.setPosition(this.ball.body, { x: PHYS.launchAnchor.x, y: PHYS.launchAnchor.y })
    Matter.Body.setVelocity(this.ball.body, { x: 0, y: 0 })
    Matter.Body.setAngularVelocity(this.ball.body, 0)
    this.phase = "aiming"
    this.ballStopSince = 0
  }

  private triggerNodeClear(): void {
    this.nodeCleared = true
    this.phase = "resolving"
    this.resolvingTimer = RESOLVE_MS
    if (this.ball) {
      // 冻结飞行中的球，停留庆祝
      Matter.Body.setStatic(this.ball.body, true)
      Matter.Body.setVelocity(this.ball.body, { x: 0, y: 0 })
    }
    const bx = this.ball?.body.position.x ?? WIDTH / 2
    const by = this.ball?.body.position.y ?? HEIGHT / 2
    this.onEvent?.({ type: "node-clear", x: bx, y: by })
  }

  /** resolving 结束：清残余钉 → 生新簇 → 球回锚 → aiming。 */
  private completeNode(): void {
    this.clearPegs()
    this.spawnPegs()
    this.respawnBall()
  }

  // ---- 生成 ----

  private clearPegs(): void {
    for (const e of this.registry.ofKind("peg-crystal")) {
      Matter.Composite.remove(this.physics.world, e.body)
      this.registry.unregister(e.id)
    }
  }

  private spawnPegs(): void {
    const specs = generateCrystalCluster()
    this.pegsTotal = specs.length
    this.nodeCleared = false
    for (const s of specs) {
      const body = Matter.Bodies.circle(s.x, s.y, PHYS.pegRadius, {
        isStatic: true,
        label: "peg-crystal",
        restitution: PHYS.pegRestitution,
        friction: 0,
      })
      Matter.Composite.add(this.physics.world, body)
      this.registry.register({ id: body.id, kind: "peg-crystal", body, hp: 1, alive: true })
    }
  }

  private spawnBall(): void {
    const body = Matter.Bodies.circle(PHYS.launchAnchor.x, PHYS.launchAnchor.y, PHYS.ballRadius, {
      label: "meteor",
      isStatic: true,
      restitution: PHYS.ballRestitution,
      friction: PHYS.ballFriction,
      frictionAir: PHYS.ballFrictionAir,
      density: PHYS.ballDensity,
      slop: PHYS.ballSlop,
    })
    Matter.Composite.add(this.physics.world, body)
    const e: Entity = { id: body.id, kind: "ball", body, hp: 1, alive: true }
    this.registry.register(e)
    this.ball = e
  }

  // ---- 碰撞 ----

  private setupCollisions(): void {
    Matter.Events.on(this.physics.engine, "collisionStart", (evt) => {
      const ballBody = this.ball?.body
      if (!ballBody) return
      for (const pair of evt.pairs) {
        const { bodyA, bodyB } = pair
        let pegBody: Matter.Body | null = null
        if (bodyA === ballBody && bodyB.label.startsWith("peg-")) pegBody = bodyB
        else if (bodyB === ballBody && bodyA.label.startsWith("peg-")) pegBody = bodyA
        if (pegBody) this.hitPeg(pegBody)
      }
    })
  }

  private hitPeg(body: Matter.Body): void {
    const e = this.registry.get(body.id)
    if (!e || !e.alive) return
    e.hp -= 1
    if (e.hp <= 0) {
      e.alive = false
      const x = body.position.x
      const y = body.position.y
      Matter.Composite.remove(this.physics.world, body)
      this.registry.unregister(body.id)
      this.score += 100
      this.onEvent?.({ type: "peg-broken", x, y, kind: e.kind })

      // 75% 清空检测
      if (!this.nodeCleared && this.pegsTotal > 0) {
        const cleared = this.pegsTotal - this.registry.countKind("peg-crystal")
        if (cleared / this.pegsTotal >= NODE_CLEAR_RATIO) this.triggerNodeClear()
      }
    }
  }

  destroy(): void {
    this.predictor.destroy()
    this.physics.destroy()
    this.registry.clear()
  }
}
