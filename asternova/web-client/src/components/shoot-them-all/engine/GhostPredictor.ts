import Matter from "matter-js"

import { HEIGHT, PHYS, WIDTH } from "../constants"
import type { EntityRegistry } from "./EntityRegistry"

export interface TrajectoryPoint {
  x: number
  y: number
}
export interface TrajectoryResult {
  points: TrajectoryPoint[]
  /** 首次碰撞在 points 中的下标，-1 表示全程未碰。 */
  firstHit: number
}

/**
 * 轨迹预测器（Stage Spec §3.4，M1 必过验收）。
 *
 * 用独立幽灵 matter 引擎，复用与 PhysicsWorld 相同的 Engine.update(fixedDelta) 积分代码，
 * 保证预测路径与真实弹道误差 <2px。幽灵球物理参数与标准陨星完全一致。
 *
 * 策略（v0.2）：推进到首碰 + 首碰后 1 次弹射（afterHitSteps），其后不再预测（保留长程混沌惊喜）。
 * 钉阵仅在 registry.version 变化时重建（O(钉数)，非每帧）。
 *
 * 后续：磁星/涡流引力（#7+）需在幽灵 step 同步施加，复用 PhysicsWorld.customForces。
 */
export class GhostPredictor {
  private ghost: Matter.Engine
  private ghostBall: Matter.Body
  private lastVersion = -1
  private hitFlag = false

  constructor(private registry: EntityRegistry) {
    this.ghost = Matter.Engine.create({
      gravity: { x: 0, y: PHYS.gravityY, scale: 0.001 },
      enableSleeping: false,
    })
    this.ghost.positionIterations = PHYS.positionIterations
    this.ghost.velocityIterations = PHYS.velocityIterations

    this.ghostBall = Matter.Bodies.circle(PHYS.launchAnchor.x, PHYS.launchAnchor.y, PHYS.ballRadius, {
      label: "ghost-ball",
      restitution: PHYS.ballRestitution,
      friction: PHYS.ballFriction,
      frictionAir: PHYS.ballFrictionAir,
      density: PHYS.ballDensity,
      slop: PHYS.ballSlop,
    })

    Matter.Events.on(this.ghost, "collisionStart", (evt) => {
      if (this.hitFlag) return
      for (const pair of evt.pairs) {
        const other = pair.bodyA === this.ghostBall ? pair.bodyB : pair.bodyA === this.ghostBall ? pair.bodyA : null
        if (other && other.label.startsWith("peg-")) {
          this.hitFlag = true
          return
        }
      }
    })

    this.rebuild()
  }

  /** 重建幽灵墙 + 当前存活钉子（仅在钉阵变化时）。 */
  private rebuild(): void {
    Matter.Composite.clear(this.ghost.world, false)
    const t = 80
    Matter.Composite.add(this.ghost.world, [
      Matter.Bodies.rectangle(WIDTH / 2, HEIGHT + t / 2, WIDTH + 240, t, {
        isStatic: true,
        label: "floor",
        restitution: 0.5,
      }),
      Matter.Bodies.rectangle(-t / 2, HEIGHT / 2, t, HEIGHT + 240, {
        isStatic: true,
        label: "wall-l",
        restitution: 0.7,
      }),
      Matter.Bodies.rectangle(WIDTH + t / 2, HEIGHT / 2, t, HEIGHT + 240, {
        isStatic: true,
        label: "wall-r",
        restitution: 0.7,
      }),
      Matter.Bodies.rectangle(WIDTH / 2, -t / 2, WIDTH + 240, t, {
        isStatic: true,
        label: "ceiling",
        restitution: 0.7,
      }),
    ])
    for (const e of this.registry.all()) {
      if (!e.alive || e.kind !== "peg-crystal") continue
      const b = Matter.Bodies.circle(e.body.position.x, e.body.position.y, PHYS.pegRadius, {
        isStatic: true,
        label: "peg-crystal",
        restitution: PHYS.pegRestitution,
        friction: 0,
      })
      Matter.Composite.add(this.ghost.world, b)
    }
    Matter.Composite.add(this.ghost.world, this.ghostBall)
    this.lastVersion = this.registry.version
  }

  private maybeRebuild(): void {
    if (this.registry.version !== this.lastVersion) this.rebuild()
  }

  /**
   * 预测从锚点以 angle 发射的轨迹。
   * 推进最多 maxSteps 步；首次撞钉后记录 firstHit，再走 afterHitSteps 步（1 次弹射）后停。
   */
  predict(angle: number, maxSteps = 48, afterHitSteps = 16): TrajectoryResult {
    this.maybeRebuild()

    Matter.Body.setPosition(this.ghostBall, { x: PHYS.launchAnchor.x, y: PHYS.launchAnchor.y })
    Matter.Body.setVelocity(this.ghostBall, {
      x: Math.sin(angle) * PHYS.v0,
      y: Math.cos(angle) * PHYS.v0,
    })
    Matter.Body.setAngularVelocity(this.ghostBall, 0)

    const points: TrajectoryPoint[] = []
    let firstHit = -1
    this.hitFlag = false

    for (let i = 0; i < maxSteps; i++) {
      this.hitFlag = false
      Matter.Engine.update(this.ghost, PHYS.fixedDelta)
      const p = this.ghostBall.position
      points.push({ x: p.x, y: p.y })
      if (this.hitFlag && firstHit < 0) firstHit = i
      if (firstHit >= 0 && i >= firstHit + afterHitSteps) break
      if (p.y > HEIGHT + 120 || p.x < -120 || p.x > WIDTH + 120) break
    }
    return { points, firstHit }
  }

  destroy(): void {
    Matter.Composite.clear(this.ghost.world, false)
    Matter.Engine.clear(this.ghost)
  }
}
