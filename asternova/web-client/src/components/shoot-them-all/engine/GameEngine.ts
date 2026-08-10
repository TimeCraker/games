import Matter from "matter-js"

import { HEIGHT, PHYS, WIDTH } from "../constants"
import { generateCrystalCluster } from "./content/pegLayouts"
import { Entity, EntityRegistry } from "./EntityRegistry"
import { GhostPredictor, TrajectoryResult } from "./GhostPredictor"
import { PhysicsWorld } from "./PhysicsWorld"

export type StaPhase = "aiming" | "flying" | "resolving" | "game-over"

/**
 * 纯 TS 游戏引擎（Stage Spec §8.1/§8.11）。
 * 持有 PhysicsWorld（matter）+ EntityRegistry + 全部逻辑。零 React/Pixi 依赖（M2 模拟器可直接 import）。
 *
 * M1 范围：发射器瞄准/发射、标准陨星物理、晶体钉碰撞破碎、球停止/出界收回、清光重生簇。
 * 后续：combo、敌人回合、遗物、节点推进（#7 + M2）。
 */
export class GameEngine {
  readonly physics = new PhysicsWorld()
  readonly registry = new EntityRegistry()

  phase: StaPhase = "aiming"
  /** 瞄准角度（弧度，0=正下方，+右 −左）。渲染层与发射器共享。 */
  aimAngle = 0
  score = 0

  private ball: Entity | null = null
  private ballStopSince = 0
  private predictor: GhostPredictor

  constructor() {
    this.setupCollisions()
    this.spawnPegs()
    this.spawnBall()
    this.predictor = new GhostPredictor(this.registry)
  }

  get ballEntity(): Entity | null {
    return this.ball
  }

  /** 轨迹预测（仅 aiming 阶段；Stage Spec §3.4，M1 必过验收）。 */
  predictTrajectory(): TrajectoryResult {
    if (this.phase !== "aiming") return { points: [], firstHit: -1 }
    return this.predictor.predict(this.aimAngle)
  }

  /** 由指针逻辑坐标设定瞄准角度（仅 aiming 阶段）。 */
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
  }

  update(dtMs: number): void {
    this.physics.step(dtMs)
    if (this.phase === "flying" && this.ball) this.tickFlying(dtMs)
  }

  private tickFlying(dtMs: number): void {
    const b = this.ball!.body
    const sp = Math.hypot(b.velocity.x, b.velocity.y)
    // 速度钳制（防穿透 + 防失控）
    if (sp > PHYS.vMax) {
      const k = PHYS.vMax / sp
      Matter.Body.setVelocity(b, { x: b.velocity.x * k, y: b.velocity.y * k })
    }

    const out =
      b.position.y > HEIGHT + 120 || b.position.x < -120 || b.position.x > WIDTH + 120
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
    // M1：清光则重生簇（#7 接 FSM + 过关判定）
    if (this.registry.countKind("peg-crystal") === 0) this.spawnPegs()
  }

  // ---- 生成 ----

  private spawnPegs(): void {
    for (const s of generateCrystalCluster()) {
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
      Matter.Composite.remove(this.physics.world, body)
      this.registry.unregister(body.id)
      this.score += 100
      // TODO #7：粒子 / 音效 / combo
    }
  }

  destroy(): void {
    this.predictor.destroy()
    this.physics.destroy()
    this.registry.clear()
  }
}
