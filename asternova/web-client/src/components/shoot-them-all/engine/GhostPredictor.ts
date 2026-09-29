import Matter from "matter-js"

import { HEIGHT, PHYS, RULES, WIDTH } from "../constants"
import { applyBallPhys } from "./PhysicsWorld"
import type { EntityRegistry } from "./EntityRegistry"
import type { BallKind } from "./types"

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
 * 轨迹预测器（白皮书 §7，误差 <2px 是验收线）。
 *
 * 用独立幽�� matter 引擎，复用与 PhysicsWorld 相同的 Engine.update(fixedDelta) 积分代码，
 * 并在每步后施加与 PhysicsWorld.maxSpeed 相同的 vMax 钳制 —— 钳制不镜像就会在
 * 加速段逐帧漂移，短程就超 2px。
 *
 * 策略：推进到首碰 + 首碰后 1 次弹射（afterHitSteps），其后不再预测（保留长程混沌惊喜）。
 * 钉阵/障碍仅在 registry.version 变化或上一轮预测临时毁钉后全量重建（O(实体数)，非每帧）。
 *
 * 与 GameEngine 的毁钉/伤害规则逐条镜像（2026-09-28 实测定案）：
 * 球是 25 边形近似圆，深穿深（单步 16px 近乎钻到钉心）时 SAT 参考面选取对
 * 「pair 的 bodyA/bodyB 顺序」和「球的顶点相位」极度敏感——两边稍有不同，
 * 碰撞法线会连方向都对不上，弹射段直接镜像分叉（实测 32px+）。因此：
 * - 幽灵球必须在 rebuild 里**最后**创建：Collision.collides 按 body.id 归一化
 *   bodyA/bodyB，实世界钉先球后（id 小），幽灵若球先钉后 pair 会翻面。
 * - 每次 predict 都把球角度归零（与 GameEngine.launch 相同），对齐顶点相位。
 * - 毁钉走 hp 伤害（含 heavy 高伤、blast 半径爆破、pierce 穿钉），与实弹同规则，
 *   否则 hp≥2 的大钉上「实弹还弹一下、幽灵钉没了」照样分叉。
 */
export class GhostPredictor {
  private ghost: Matter.Engine
  private ghostBall!: Matter.Body // rebuild() 末尾创建（id 必须大于钉，见类注释）
  private lastVersion = -1
  private sensorMode = false
  private hitFlag = false
  /** 本轮预测的球种（决定伤害镜像） */
  private currentKind: BallKind = "standard"
  private blastUsed = false
  /** 幽灵钉/障碍的剩余 hp（镜像注册表实体 hp；key=幽灵 body.id） */
  private ghostHp = new Map<number, number>()
  /** 本轮预测中临时移除的实体（预测结束不回填，下次 rebuild 从注册表重生） */
  private removed: Matter.Body[] = []

  constructor(private registry: EntityRegistry) {
    this.ghost = Matter.Engine.create({
      gravity: { x: 0, y: PHYS.gravityY, scale: 0.001 },
      enableSleeping: false,
    })
    this.ghost.positionIterations = PHYS.positionIterations
    this.ghost.velocityIterations = PHYS.velocityIterations

    Matter.Events.on(this.ghost, "collisionStart", (evt) => {
      for (const pair of evt.pairs) {
        const other =
          pair.bodyA === this.ghostBall ? pair.bodyB : pair.bodyB === this.ghostBall ? pair.bodyA : null
        if (!other) continue
        if (other.label.startsWith("peg-")) {
          this.hitFlag = true
          // pierce：钉是传感器（无求解反弹），穿钉仍计伤害/击碎
          if (this.sensorMode) {
            this.damageGhostPeg(other, this.currentDamage())
            continue
          }
          if (this.currentKind === "blast" && !this.blastUsed) {
            // 镜像 GameEngine.hitPeg 的爆裂：以命中点为中心清场（无视 hp 直接碎）
            this.blastUsed = true
            const cx = other.position.x
            const cy = other.position.y
            for (const b of [...Matter.Composite.allBodies(this.ghost.world)]) {
              if (!b.label.startsWith("peg-")) continue
              if (Math.hypot(b.position.x - cx, b.position.y - cy) <= RULES.blastRadius) {
                this.breakGhostPeg(b)
              }
            }
            continue
          }
          this.damageGhostPeg(other, this.currentDamage())
        } else if (other.label.startsWith("obstacle-")) {
          // 首碰标记含障碍（撞击点预览要落在第一个撞上的实体上）
          this.hitFlag = true
          // 镜像 hitObstacle：仅 heavy 掉障碍 hp，其他球纯弹开
          if (this.currentKind === "heavy") {
            this.damageGhostObstacle(other, RULES.heavyObstacleDamage)
          }
        }
      }
    })

    this.rebuild()
  }

  private currentDamage(): number {
    return RULES.pegDamage[this.currentKind]
  }

  /** 镜像 destroyPeg：直接破碎移出（hp 无视）。 */
  private breakGhostPeg(body: Matter.Body): void {
    Matter.Composite.remove(this.ghost.world, body)
    this.ghostHp.delete(body.id)
    this.removed.push(body)
  }

  /** 镜像 hitPeg 的 hp 伤害路径。 */
  private damageGhostPeg(body: Matter.Body, dmg: number): void {
    const hp = (this.ghostHp.get(body.id) ?? 1) - dmg
    if (hp <= 0) this.breakGhostPeg(body)
    else this.ghostHp.set(body.id, hp)
  }

  /** 镜像 hitObstacle 的 hp 伤害路径。 */
  private damageGhostObstacle(body: Matter.Body, dmg: number): void {
    const hp = (this.ghostHp.get(body.id) ?? 1) - dmg
    if (hp <= 0) {
      Matter.Composite.remove(this.ghost.world, body)
      this.ghostHp.delete(body.id)
      this.removed.push(body)
    } else {
      this.ghostHp.set(body.id, hp)
    }
  }

  /** 重建幽灵墙 + 当前存活钉/障碍 + 幽灵球（球最后建，保 pair 顺序与实世界一致）。 */
  private rebuild(): void {
    this.removed.length = 0
    this.ghostHp.clear()
    Matter.Composite.clear(this.ghost.world, false)
    const t = 80
    Matter.Composite.add(this.ghost.world, [
      Matter.Bodies.rectangle(WIDTH / 2, HEIGHT + t / 2, WIDTH + 240, t, {
        isStatic: true,
        label: "floor",
        restitution: 0.5,
        friction: 0.1,
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
      if (!e.alive) continue
      if (e.kind.startsWith("peg-")) {
        const b = Matter.Bodies.circle(e.body.position.x, e.body.position.y, PHYS.pegRadius, {
          isStatic: true,
          label: e.kind,
          restitution: PHYS.pegRestitution,
          friction: 0,
        })
        Matter.Composite.add(this.ghost.world, b)
        this.ghostHp.set(b.id, e.hp)
      } else if (e.kind.startsWith("obstacle-")) {
        const w = (e.meta?.w as number) ?? e.body.bounds.max.x - e.body.bounds.min.x
        const h = (e.meta?.h as number) ?? e.body.bounds.max.y - e.body.bounds.min.y
        const b = Matter.Bodies.rectangle(e.body.position.x, e.body.position.y, w, h, {
          isStatic: true,
          label: e.kind,
          restitution: 0.5,
          friction: 0.1,
        })
        Matter.Composite.add(this.ghost.world, b)
        this.ghostHp.set(b.id, e.hp)
      }
    }
    // ⚠️ 幽灵球必须最后创建：Collision.collides 用 body.id 大小归一化 pair 的
    // bodyA/bodyB（id 小的做 bodyA）。实世界是「先建钉、后建球」→ pair=(peg, ball)；
    // 幽灵球若在构造器里先建就会 pair=(ball, peg)，SAT 参考面翻转，
    // 深穿深时碰撞法线连方向都不同（实测首碰弹射段 32px 镜像分叉）。
    this.ghostBall = Matter.Bodies.circle(PHYS.launchAnchor.x, PHYS.launchAnchor.y, PHYS.ballRadius, {
      label: "ghost-ball",
      restitution: PHYS.ballRestitution,
      friction: PHYS.ballFriction,
      frictionAir: PHYS.ballFrictionAir,
      density: PHYS.ballDensity,
      slop: PHYS.ballSlop,
    })
    Matter.Composite.add(this.ghost.world, this.ghostBall)
    this.lastVersion = this.registry.version
    this.applySensorMode()
  }

  /** pierce 语义：钉变传感器（有碰撞事件、无求解反弹）。 */
  private applySensorMode(): void {
    for (const b of Matter.Composite.allBodies(this.ghost.world)) {
      if (b.label.startsWith("peg-")) b.isSensor = this.sensorMode
    }
  }

  private maybeRebuild(ballKind: BallKind): void {
    const wantSensor = ballKind === "pierce"
    // 全量重建三条件：传感器模式切换（pair.isSensor 是创建时快照）、注册表变化、
    // 上轮预测临时毁过钉（部分回填会打乱 bodies 顺序 → pair 归一化跟着乱）。
    if (wantSensor !== this.sensorMode || this.registry.version !== this.lastVersion || this.removed.length) {
      this.sensorMode = wantSensor
      this.rebuild()
    }
  }

  /**
   * 预测从锚点以 angle 发射的轨迹（ballKind 决定穿钉/爆破/高伤语义）。
   * 推进最多 maxSteps 步；首次撞钉后记录 firstHit，再走 afterHitSteps 步后停。
   */
  predict(angle: number, ballKind: BallKind = "standard", maxSteps = 48, afterHitSteps = 16): TrajectoryResult {
    this.currentKind = ballKind
    this.blastUsed = false
    this.maybeRebuild(ballKind)

    // 与 GameEngine.launch 相同的球体正则化：25 边形近似圆的顶点相位若带着
    // 上一发的残余自转，SAT 选面会与实弹不同 → 归零对齐。
    Matter.Body.setAngle(this.ghostBall, 0)
    // 球种手感（BALL_PHYS）与实弹同源施加，逐条镜像保 <2px 轨迹精度。
    applyBallPhys(this.ghostBall, ballKind)
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
      // 与 PhysicsWorld.step 相同的 vMax 钳制（每固定步），保证与实弹逐帧同轨
      const bv = this.ghostBall.velocity
      const sp = Math.hypot(bv.x, bv.y)
      if (sp > PHYS.vMax) {
        const k = PHYS.vMax / sp
        Matter.Body.setVelocity(this.ghostBall, { x: bv.x * k, y: bv.y * k })
      }
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
