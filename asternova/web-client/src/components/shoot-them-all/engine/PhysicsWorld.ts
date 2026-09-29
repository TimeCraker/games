import Matter from "matter-js"

import { BALL_PHYS, HEIGHT, PHYS, WIDTH } from "../constants"
import type { BallKind } from "./types"

/** 自定义力（磁星/涡流引力，每子步施加到非静态体）。引擎层零 Pixi 依赖。 */
export type CustomForceFn = (body: Matter.Body, deltaMs: number) => void

/**
 * 按球种套用手感参数（BALL_PHYS 单点表）。
 *
 * ⚠️ 镜像红线：GameEngine.launch（实弹）与 GhostPredictor.predict（幽灵球）必须
 * 都走本函数，逐条同值才保 <2px 轨迹精度。实弹侧必须在 setStatic(false) **之后**
 * 调用——matter 的 setStatic(false) 会用 _original 快照还原 restitution/friction/
 * density，提前设置会被覆盖回标准值。
 */
export function applyBallPhys(body: Matter.Body, kind: BallKind): void {
  const p = BALL_PHYS[kind]
  body.restitution = p.restitution
  body.friction = p.friction
  body.frictionAir = p.frictionAir
  Matter.Body.setDensity(body, p.density)
}

/**
 * matter 物理世界（Stage Spec §3.2/§8.5）。
 *
 * 关键：手动固定步长推进（不用 matter Runner），使轨迹预测（§3.4/#6）能复用同一段积分代码。
 * 累加器把可变帧时间转为固定 FIXED_DELTA 步，最多补 5 步防 spiral；帧时间尖峰（切后台）钳到 100ms。
 */
export class PhysicsWorld {
  readonly engine: Matter.Engine
  readonly world: Matter.World

  private customForces: CustomForceFn[] = []
  private accumulator = 0

  /**
   * 非静态体速度上限（px/步），每固定子步后钳制；null = 不钳制。
   * 必须逐子步钳（而不是每帧钳一次）：GhostPredictor.predict 的幽灵球就是逐子步钳的，
   * 两边节奏不一致会在加速段逐帧漂移，轨迹预测误差直接超 2px 验收线。
   */
  maxSpeed: number | null = null

  constructor() {
    this.engine = Matter.Engine.create({
      gravity: { x: 0, y: PHYS.gravityY, scale: 0.001 },
      enableSleeping: false,
    })
    this.engine.positionIterations = PHYS.positionIterations
    this.engine.velocityIterations = PHYS.velocityIterations
    this.engine.constraintIterations = PHYS.constraintIterations
    this.world = this.engine.world

    this.addBoundaries()
  }

  /** 四面墙体（Stage Spec §3.1 画布 720×1280）。底部为重力舱区域，M1 暂用反弹墙，#7 换接球槽。 */
  private addBoundaries() {
    const t = 80
    const walls = [
      Matter.Bodies.rectangle(WIDTH / 2, HEIGHT + t / 2, WIDTH + 240, t, {
        isStatic: true,
        label: "floor",
        restitution: 0.5,
        friction: 0.1,
        render: { visible: false },
      }),
      Matter.Bodies.rectangle(-t / 2, HEIGHT / 2, t, HEIGHT + 240, {
        isStatic: true,
        label: "wall-l",
        restitution: 0.7,
        render: { visible: false },
      }),
      Matter.Bodies.rectangle(WIDTH + t / 2, HEIGHT / 2, t, HEIGHT + 240, {
        isStatic: true,
        label: "wall-r",
        restitution: 0.7,
        render: { visible: false },
      }),
      Matter.Bodies.rectangle(WIDTH / 2, -t / 2, WIDTH + 240, t, {
        isStatic: true,
        label: "ceiling",
        restitution: 0.7,
        render: { visible: false },
      }),
    ]
    Matter.Composite.add(this.world, walls)
  }

  addCustomForce(fn: CustomForceFn): void {
    this.customForces.push(fn)
  }

  /** 固定步长推进。dtMs 为本帧实际耗时（毫秒）。 */
  step(dtMs: number): void {
    this.accumulator += Math.min(dtMs, 100)
    let steps = 0
    while (this.accumulator >= PHYS.fixedDelta && steps < 5) {
      this.applyCustomForces(PHYS.fixedDelta)
      Matter.Engine.update(this.engine, PHYS.fixedDelta)
      // 逐子步钳速：与 GhostPredictor.predict 同节奏，保证预测与实弹同轨
      if (this.maxSpeed !== null) {
        for (const b of Matter.Composite.allBodies(this.world)) {
          if (b.isStatic) continue
          const sp = Math.hypot(b.velocity.x, b.velocity.y)
          if (sp > this.maxSpeed) {
            const k = this.maxSpeed / sp
            Matter.Body.setVelocity(b, { x: b.velocity.x * k, y: b.velocity.y * k })
          }
        }
      }
      this.accumulator -= PHYS.fixedDelta
      steps++
    }
    if (steps >= 5) this.accumulator = 0
  }

  private applyCustomForces(deltaMs: number): void {
    if (this.customForces.length === 0) return
    const bodies = Matter.Composite.allBodies(this.world)
    for (const b of bodies) {
      if (b.isStatic) continue
      for (const fn of this.customForces) fn(b, deltaMs)
    }
  }

  destroy(): void {
    Matter.Composite.clear(this.world, false)
    Matter.Engine.clear(this.engine)
  }
}
