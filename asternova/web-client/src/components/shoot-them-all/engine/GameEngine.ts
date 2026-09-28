import Matter from "matter-js"

import { HEIGHT, PHYS, RULES, WIDTH } from "../constants"
import { getLevel, LEVELS } from "./content/levels"
import { Entity, EntityRegistry } from "./EntityRegistry"
import { GhostPredictor, TrajectoryResult } from "./GhostPredictor"
import { PhysicsWorld } from "./PhysicsWorld"
import type { BallKind, EngineEvent, LevelDef, ObstacleKind, PegKind, StaHudState, StaPhase } from "./types"

export type { BallKind, EngineEvent, StaHudState, StaPhase } from "./types"

/** 球落定/出界后到下一球的短暂停顿（ms，留给 UI 播反馈）。 */
const RESOLVE_MS = 400

/** 实体 kind（matter label）→ 计分用的钉种类。 */
function pegKindOf(kind: string): PegKind {
  return kind.replace("peg-", "") as PegKind
}

/**
 * 弹珠风暴 —— 关卡制弹射消消乐引擎（白皮书定稿版）。
 *
 * 纯 TS，零 React/Pixi 依赖。核心循环（白皮书 §2/§5/§7）：
 * aiming（选球/瞄准/发射）→ flying（弹跳清钉得分）→ resolving（短停顿）→ aiming；
 * 分数 ≥ 目标分的瞬间 → level-clear（按未打出球数给星）；
 * 球全部打完仍 < 目标分 → level-fail。level-clear / level-fail 为终态，
 * 由 UI 调 restartLevel()/nextLevel() 推进。
 *
 * 球种技能（白皮书 §4）：
 * - standard：基础弹跳。
 * - blast：命中第一颗钉时以命中点为中心爆破（清半径内钉，一次性）。
 * - pierce：飞行期钉阵临时变为传感器 → 穿钉不减速不反弹，逐颗击碎（一次性触发技能事件）。
 * - heavy：对钉 2 点伤害（可秒 hp=2 大钉），且是唯一能对障碍造成伤害的球。
 */
export class GameEngine {
  readonly physics = new PhysicsWorld()
  readonly registry = new EntityRegistry()

  phase: StaPhase = "aiming"
  aimAngle = 0
  score = 0
  /** 供渲染层订阅的事件回调。 */
  onEvent: ((e: EngineEvent) => void) | null = null

  private level: LevelDef
  private levelId: number
  /** 未打出的球种队列（按打出顺序）；queue[0] = 当前选中球 */
  private queue: BallKind[] = []
  /** 在飞/被冻结的球种；null = 没有球在场上动作 */
  private flyingKind: BallKind | null = null
  private ball: Entity | null = null
  private ballStopSince = 0
  private combo = 0
  private bestCombo = 0
  private stars = 0
  private pegsTotal = 0
  private resolvingTimer = 0
  private predictor: GhostPredictor
  // 每颗球一次性的技能触发标记（launch 时重置）
  private blastUsed = false
  private pierceSkillFired = false
  private heavySkillFired = false

  constructor() {
    this.setupCollisions()
    // 逐子步钳速下沉到 PhysicsWorld（与 GhostPredictor.predict 同节奏），
    // 预测误差验收线 <2px 要求两边逐帧同轨。
    this.physics.maxSpeed = PHYS.vMax
    this.level = LEVELS[0]
    this.levelId = LEVELS[0].id
    this.predictor = new GhostPredictor(this.registry)
    this.startLevel(this.levelId)
  }

  get ballEntity(): Entity | null {
    return this.ball
  }

  /** 场上剩余钉数（所有钉种类，不含障碍）。 */
  get pegsLeft(): number {
    let n = 0
    for (const e of this.registry.all()) {
      if (e.kind.startsWith("peg-")) n++
    }
    return n
  }

  /**
   * HUD 只读快照。全部取自引擎真实状态，不是装饰数字。
   * ballsLeft = 未打出的球数（含即将打出的当前球）—— 在飞的球已算打出。
   */
  hudSnapshot(): StaHudState {
    return {
      phase: this.phase,
      levelId: this.level.id,
      levelName: this.level.name,
      score: this.score,
      targetScore: this.level.targetScore,
      ballsLeft: this.queue.length,
      ballQueue: [...this.queue],
      currentBall: this.flyingKind ?? this.queue[0] ?? null,
      combo: this.combo,
      bestCombo: this.bestCombo,
      pegsLeft: this.pegsLeft,
      pegsTotal: this.pegsTotal,
      progress: this.level.targetScore > 0 ? Math.min(1, this.score / this.level.targetScore) : 0,
      stars: this.stars,
    }
  }

  predictTrajectory(): TrajectoryResult {
    if (this.phase !== "aiming") return { points: [], firstHit: -1 }
    return this.predictor.predict(this.aimAngle, this.queue[0] ?? "standard")
  }

  setAimFromPoint(px: number, py: number): void {
    if (this.phase !== "aiming") return
    const dx = px - PHYS.launchAnchor.x
    const dy = Math.max(1, py - PHYS.launchAnchor.y)
    const theta = Math.atan2(dx, dy)
    this.aimAngle = Math.max(-PHYS.angleMax, Math.min(PHYS.angleMax, theta))
  }

  /**
   * 从剩余队列选中该球种的下一颗：把第一颗该球种换到队首（同种球等价，
   * 换位即「选中」）。没有该球种 / 已在队首 / 非 aiming → no-op。
   */
  selectBall(kind: BallKind): void {
    if (this.phase !== "aiming") return
    const idx = this.queue.indexOf(kind)
    if (idx <= 0) return
    const tmp = this.queue[0]
    this.queue[0] = this.queue[idx]
    this.queue[idx] = tmp
  }

  launch(): void {
    if (this.phase !== "aiming" || !this.ball || this.queue.length === 0) return
    const kind = this.queue.shift()!
    this.flyingKind = kind
    this.combo = 0
    this.blastUsed = false
    this.pierceSkillFired = false
    this.heavySkillFired = false

    const body = this.ball.body
    body.frictionAir = kind === "pierce" ? 0 : PHYS.ballFrictionAir // 穿透弹「不衰减」
    // 穿透弹飞行期把钉临时变传感器：matter 传感器对只发碰撞事件、不产生求解反弹，
    // 于是「穿钉不减速不反弹」由物理层直接保证，而不是事后抵消冲量。
    this.setPegSensors(kind === "pierce")

    const v = PHYS.v0
    Matter.Body.setStatic(body, false)
    // 顶点相位对齐：球是 25 边形近似圆，带着残余自转会让 SAT 选面与幽灵预测不同
    // （实测首碰弹射段镜像分叉 32px+），每发归零。
    Matter.Body.setAngle(body, 0)
    Matter.Body.setVelocity(body, {
      x: Math.sin(this.aimAngle) * v,
      y: Math.cos(this.aimAngle) * v,
    })
    Matter.Body.setAngularVelocity(body, 0)
    this.phase = "flying"
    this.ballStopSince = 0
    this.onEvent?.({ type: "launch", ball: kind })
  }

  update(dtMs: number): void {
    this.physics.step(dtMs)

    if (this.phase === "flying") {
      this.tickFlying(dtMs)
    } else if (this.phase === "resolving") {
      this.resolvingTimer -= dtMs
      if (this.resolvingTimer <= 0) this.finishResolving()
    }
    // level-clear / level-fail 是终态：物理照常步进（冻结的球是静态体），
    // 等 UI 调 restartLevel()/nextLevel()，引擎不自行推进。
  }

  private tickFlying(dtMs: number): void {
    const b = this.ball!.body
    // vMax 钳制在 PhysicsWorld.step 逐子步做（与预测同轨），这里只管出界/停球
    const sp = Math.hypot(b.velocity.x, b.velocity.y)
    const out = b.position.y > HEIGHT + 120 || b.position.x < -120 || b.position.x > WIDTH + 120
    if (out) {
      this.endBall()
      return
    }
    if (sp < 0.3) {
      this.ballStopSince += dtMs
      if (this.ballStopSince > 600) this.endBall()
    } else {
      this.ballStopSince = 0
    }
  }

  /** 一次出手结束：钉阵传感器复位 → 有球则短暂 resolving 后回 aiming，无球则判负。 */
  private endBall(): void {
    this.setPegSensors(false)
    this.flyingKind = null
    this.combo = 0
    if (this.ball) {
      Matter.Body.setStatic(this.ball.body, true)
      Matter.Body.setVelocity(this.ball.body, { x: 0, y: 0 })
      Matter.Body.setAngularVelocity(this.ball.body, 0)
    }
    this.ballStopSince = 0

    if (this.queue.length === 0) {
      // 球全部打完：达标已在击碎判定瞬间进 level-clear，这里只可能是未达标。
      this.triggerLevelFail()
      return
    }
    this.phase = "resolving"
    this.resolvingTimer = RESOLVE_MS
  }

  private finishResolving(): void {
    this.parkBallAtLauncher()
    this.phase = "aiming"
  }

  // ---- 关卡生命周期 ----

  startLevel(levelId: number): void {
    const def = getLevel(levelId)
    // 越界/未知 id → no-op（回第 1 关之类的行为交给 UI 决定，引擎保持当前局不动）
    if (!def) return
    this.clearBoard()
    this.level = def
    this.levelId = def.id
    this.score = 0
    this.combo = 0
    this.bestCombo = 0
    this.stars = 0
    this.flyingKind = null
    this.queue = [...def.balls]
    this.spawnPegs(def.pegs)
    this.spawnObstacles(def.obstacles)
    this.pegsTotal = this.pegsLeft
    this.spawnBall()
    this.phase = "aiming"
    this.ballStopSince = 0
    this.resolvingTimer = 0
  }

  restartLevel(): void {
    this.startLevel(this.levelId)
  }

  /** 下一关；已是最后一关则回第 1 关（首发无终局画面，循环重打保证「下一关」按钮永远可用）。 */
  nextLevel(): void {
    const idx = LEVELS.findIndex((l) => l.id === this.levelId)
    const next = LEVELS[(idx + 1) % LEVELS.length]
    this.startLevel(next.id)
  }

  destroy(): void {
    this.predictor.destroy()
    this.physics.destroy()
    this.registry.clear()
  }

  // ---- 胜负 ----

  /** 任意得分后判定：分数 ≥ 目标分的瞬间立刻过关（白皮书 §5）。 */
  private checkWin(): void {
    if (this.phase !== "flying" && this.phase !== "resolving") return
    if (this.score >= this.level.targetScore) this.triggerLevelClear()
  }

  private triggerLevelClear(): void {
    // 冻结飞行中的球，原地庆祝
    if (this.ball) {
      Matter.Body.setStatic(this.ball.body, true)
      Matter.Body.setVelocity(this.ball.body, { x: 0, y: 0 })
    }
    this.setPegSensors(false)
    // 星级按未打出的剩余球数（在飞的球算已打出）：≥2=3★、1=2★、0=1★
    const left = this.queue.length
    this.stars = left >= 2 ? 3 : left === 1 ? 2 : 1
    this.phase = "level-clear"
    this.onEvent?.({ type: "level-clear", stars: this.stars, score: this.score, ballsLeft: left })
  }

  private triggerLevelFail(): void {
    this.phase = "level-fail"
    this.onEvent?.({ type: "level-fail", score: this.score, targetScore: this.level.targetScore })
  }

  // ---- 生成 / 清场 ----

  private clearBoard(): void {
    if (this.ball) {
      Matter.Composite.remove(this.physics.world, this.ball.body)
      this.registry.unregister(this.ball.id)
      this.ball = null
    }
    for (const e of this.registry.all()) {
      Matter.Composite.remove(this.physics.world, e.body)
    }
    this.registry.clear()
    this.setPegSensors(false) // 空表循环，等价于复位保险
  }

  private spawnPegs(specs: LevelDef["pegs"]): void {
    for (const s of specs) {
      const body = Matter.Bodies.circle(s.x, s.y, PHYS.pegRadius, {
        isStatic: true,
        label: `peg-${s.kind}`,
        restitution: PHYS.pegRestitution,
        friction: 0,
      })
      Matter.Composite.add(this.physics.world, body)
      this.registry.register({
        id: body.id,
        kind: `peg-${s.kind}`,
        body,
        hp: s.hp ?? 1,
        alive: true,
        meta: { pegKind: s.kind },
      })
    }
  }

  private spawnObstacles(specs: LevelDef["obstacles"]): void {
    for (const s of specs) {
      const body = Matter.Bodies.rectangle(s.x, s.y, s.w, s.h, {
        isStatic: true,
        label: `obstacle-${s.kind}`,
        restitution: 0.5,
        friction: 0.1,
      })
      Matter.Composite.add(this.physics.world, body)
      this.registry.register({
        id: body.id,
        kind: `obstacle-${s.kind}`,
        body,
        hp: s.hp,
        alive: true,
        meta: { w: s.w, h: s.h, obstacleKind: s.kind },
      })
    }
  }

  private spawnBall(): void {
    // ⚠️ 不要在这里写 isStatic: true（2026-09-27 修）。
    //
    // matter-js 0.20 的 Body.create 先在 Common.extend 阶段把 options.isStatic 拷进 body，
    // 随后 _initProperties 才调用 Body.setStatic(body, true)；而 setStatic 记录恢复快照的
    // 条件是 `if (!part.isStatic)` —— 此时它已经是 true，于是 `_original` 从未被记录。
    // 后果：之后任何 setStatic(body, false) 都命中 `else if (part._original)` 为空而变成空操作，
    // 质量/摩擦/弹性永远停在静态值（mass=Infinity、friction=1、restitution=0）。
    // 一旦 launch() 给它赋速度，重力累加得到 force=Infinity，Body.update 里
    // `force / mass` = Infinity/Infinity = NaN，位置与速度永久污染成 NaN：
    // 球的速度判定 / 出界判定 / 静止判定全部失效，**每次打开页面只能开一炮，之后永久卡死**。
    //
    // 正确做法：先建动态体，再显式 setStatic(true)，这样 _original 才会被正确记录。
    const body = Matter.Bodies.circle(PHYS.launchAnchor.x, PHYS.launchAnchor.y, PHYS.ballRadius, {
      label: "ball",
      restitution: PHYS.ballRestitution,
      friction: PHYS.ballFriction,
      frictionAir: PHYS.ballFrictionAir,
      density: PHYS.ballDensity,
      slop: PHYS.ballSlop,
    })
    Matter.Composite.add(this.physics.world, body)
    // 关键：显式转静态，这样 setStatic 才会把动态期的质量/摩擦/弹性记进 _original，
    // launch() 里的 setStatic(body, false) 才有东西可恢复。
    Matter.Body.setStatic(body, true)
    const e: Entity = {
      id: body.id,
      kind: "ball",
      body,
      hp: 1,
      alive: true,
      meta: { ballKind: this.queue[0] ?? "standard" },
    }
    this.registry.register(e)
    this.ball = e
  }

  /** 把球收回发射锚点（选球换种只换 meta，不重建刚体）。 */
  private parkBallAtLauncher(): void {
    if (!this.ball) {
      this.spawnBall()
      return
    }
    const body = this.ball.body
    Matter.Body.setStatic(body, true)
    Matter.Body.setPosition(body, { x: PHYS.launchAnchor.x, y: PHYS.launchAnchor.y })
    Matter.Body.setVelocity(body, { x: 0, y: 0 })
    Matter.Body.setAngularVelocity(body, 0)
    body.frictionAir = PHYS.ballFrictionAir
    this.ball.meta = { ballKind: this.queue[0] ?? "standard" }
  }

  // ---- 碰撞 ----

  private setPegSensors(on: boolean): void {
    for (const e of this.registry.all()) {
      if (e.kind.startsWith("peg-")) e.body.isSensor = on
    }
  }

  private setupCollisions(): void {
    Matter.Events.on(this.physics.engine, "collisionStart", (evt) => {
      const ballBody = this.ball?.body
      if (!ballBody) return
      for (const pair of evt.pairs) {
        const { bodyA, bodyB } = pair
        let other: Matter.Body | null = null
        if (bodyA === ballBody) other = bodyB
        else if (bodyB === ballBody) other = bodyA
        if (!other) continue
        if (other.label.startsWith("peg-")) this.hitPeg(other)
        else if (other.label.startsWith("obstacle-")) this.hitObstacle(other)
      }
    })
  }

  private hitPeg(body: Matter.Body): void {
    const e = this.registry.get(body.id)
    if (!e || !e.alive) return
    const kind = this.flyingKind ?? "standard"

    if (kind === "blast" && !this.blastUsed) {
      // 爆裂弹：命中第一颗钉时以命中点为中心清场，球继续正常飞行（仅爆一次）。
      this.blastUsed = true
      const cx = body.position.x
      const cy = body.position.y
      this.onEvent?.({ type: "skill", skill: "blast", x: cx, y: cy })
      for (const p of [...this.registry.all()]) {
        if (!p.kind.startsWith("peg-") || !p.alive) continue
        const d = Math.hypot(p.body.position.x - cx, p.body.position.y - cy)
        if (d <= RULES.blastRadius) this.destroyPeg(p)
      }
      return
    }

    if (kind === "pierce" && !this.pierceSkillFired) {
      this.pierceSkillFired = true
      this.onEvent?.({ type: "skill", skill: "pierce", x: body.position.x, y: body.position.y })
    }

    e.hp -= RULES.pegDamage[kind]
    if (e.hp <= 0) this.destroyPeg(e)
  }

  private destroyPeg(e: Entity): void {
    if (!e.alive) return
    e.alive = false
    const x = e.body.position.x
    const y = e.body.position.y
    Matter.Composite.remove(this.physics.world, e.body)
    this.registry.unregister(e.id)

    // 连击：同一次出手内第 n 颗 ×(1+0.1*(n-1))，封顶 2×
    this.combo += 1
    if (this.combo > this.bestCombo) this.bestCombo = this.combo
    const mult = Math.min(RULES.comboCap, 1 + RULES.comboStep * (this.combo - 1))
    const base = RULES.pegScore[pegKindOf(e.kind)]
    const gained = Math.round(base * mult)
    this.score += gained

    this.onEvent?.({ type: "peg-broken", x, y, kind: pegKindOf(e.kind), score: gained })
    this.onEvent?.({ type: "combo", value: this.combo })
    this.checkWin()
  }

  private hitObstacle(body: Matter.Body): void {
    // 白皮书 §7：其他球碰障碍只是弹开（纯物理，无事件）；只有 heavy 掉障碍 hp。
    if ((this.flyingKind ?? "standard") !== "heavy") return
    const e = this.registry.get(body.id)
    if (!e || !e.alive) return

    const x = body.position.x
    const y = body.position.y
    if (!this.heavySkillFired) {
      this.heavySkillFired = true
      this.onEvent?.({ type: "skill", skill: "heavy", x, y })
    }

    e.hp -= RULES.heavyObstacleDamage
    const destroyed = e.hp <= 0
    if (destroyed) {
      e.alive = false
      Matter.Composite.remove(this.physics.world, e.body)
      this.registry.unregister(e.id)
      this.score += RULES.obstacleScore
    }
    this.onEvent?.({
      type: "obstacle-hit",
      x,
      y,
      kind: (e.meta?.obstacleKind as ObstacleKind) ?? "stone",
      destroyed,
    })
    if (destroyed) this.checkWin()
  }
}
