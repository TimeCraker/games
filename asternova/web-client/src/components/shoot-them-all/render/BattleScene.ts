import { Container, Graphics, Sprite, Text } from "pixi.js"

import { HEIGHT, PALETTE, PHYS, WIDTH } from "../constants"
import type { EngineEvent, GameEngine } from "../engine/GameEngine"
import type { Entity } from "../engine/EntityRegistry"
import { ART, ballTexture, glowTexture, pegTexture } from "./artAssets"
import { easeOut, FxLayer } from "./FxLayer"
import { ParticleSystem } from "./ParticleSystem"

type BallKind = "standard" | "blast" | "pierce" | "heavy"

/** 拖尾历史环缓冲（预分配，零每帧分配；art bible §3.1）。 */
const TRAIL_CAP = 48

interface TimedFx {
  t: number
  fn: () => void
}

/**
 * 战斗场景渲染层（art bible §3 全量视觉规格）。
 * 每帧从 GameEngine 同步 + 订阅 engine.onEvent 驱动 Juice；引擎层零 Pixi，渲染层零物理。
 */
export class BattleScene {
  readonly container = new Container()
  /** 全屏覆盖层（闪白/变暗/星级）——钉在屏幕上，交由 StaPixiApp 挂 stage 顶层 */
  readonly overlay: Container

  private pegLayer = new Container()
  private obstacleLayer = new Container()
  private trajectory = new Graphics()
  private trailG = new Graphics()
  private particles = new ParticleSystem()
  private ballLayer = new Container()
  private launcher = new Container()
  private fx = new FxLayer()

  // 星象仪五件套（art bible §3.5）
  private barrelGroup = new Container()
  private barrelRecoil = 0
  private chargeRings!: Graphics // buildLauncher() 内构造
  private chargeFlash = 0
  private scaleArc!: Graphics // buildLauncher() 内构造
  private gemCore!: Sprite // buildLauncher() 内构造

  private pegSprites = new Map<number, Sprite>()
  private pegFlashG = new Graphics() // 击钉闪白/裂纹/共鸣呼吸环叠加（逐帧重绘）
  private obstacleSprites = new Map<number, Container>()
  private obstacleHp = new Map<number, number>()
  private obstacleTremble = new Map<number, number>()
  private lastPhase = ""

  private ballGlow: Sprite
  private ballSprite: Sprite
  private ballKind: BallKind = "standard"
  private flyingKind: BallKind | null = null

  // 拖尾环缓冲
  private trailX = new Float32Array(TRAIL_CAP)
  private trailY = new Float32Array(TRAIL_CAP)
  private trailT = new Float32Array(TRAIL_CAP)
  private trailHead = 0
  private trailCount = 0
  private heavyStep = 0
  private elapsed = 0

  private pierceMarks: Array<{ x: number; y: number; angle: number; life: number }> = []
  private pending: TimedFx[] = []
  /** 调试/取证钩子：true 时跳过本帧世界时钟（画布保留最后一帧，供截图取「特效瞬间」） */
  frozen = false
  private clearBanner: Text
  private bannerAlpha = 0
  private lastMarkerX = 0
  private markerPop = 0
  private reducedMotion = false

  constructor(private readonly engine: GameEngine) {
    this.reducedMotion = this.fx.reducedMotion
    this.overlay = this.fx.overlay

    this.container.addChild(this.obstacleLayer)
    this.container.addChild(this.pegLayer)
    this.container.addChild(this.pegFlashG)
    this.container.addChild(this.trajectory)
    this.container.addChild(this.trailG)
    this.container.addChild(this.particles.container)
    this.container.addChild(this.ballLayer)
    this.container.addChild(this.launcher)
    this.container.addChild(this.fx.container)

    this.launcher.position.set(PHYS.launchAnchor.x, PHYS.launchAnchor.y)
    this.buildLauncher()

    this.ballGlow = new Sprite({ texture: glowTexture(22, "ball") })
    this.ballGlow.anchor.set(0.5)
    this.ballGlow.blendMode = "add"
    this.ballGlow.alpha = 0.25
    this.ballSprite = new Sprite({ texture: ballTexture("standard") })
    this.ballSprite.anchor.set(0.5)
    this.ballSprite.scale.set(0.5)
    this.ballLayer.addChild(this.ballGlow, this.ballSprite)

    this.clearBanner = new Text({
      text: "CLEAR",
      style: {
        fontFamily: "Orbitron, 'PingFang SC', sans-serif",
        fontSize: 48,
        fontWeight: "bold",
        fill: PALETTE.amberBright,
        letterSpacing: 3, // 0.06em ≈ 3px @48
        stroke: { color: PALETTE.amber, width: 2 },
      },
    })
    this.clearBanner.anchor.set(0.5)
    this.clearBanner.position.set(WIDTH / 2, HEIGHT * 0.34)
    this.clearBanner.alpha = 0
    this.container.addChild(this.clearBanner)
  }

  // ---- 星象仪（art bible §3.5 五件套） ----

  private buildLauncher(): void {
    // 1) 黄铜梯形接口（上宽 48 下宽 36，自胶囊底部探出 12px）
    const base = new Graphics()
    base
      .poly([-24, 24, 24, 24, 18, 36, -18, 36])
      .fill({ color: ART.brass, alpha: 1 })
      .stroke({ width: 1, color: ART.ink500, alpha: 0.9 })
    this.launcher.addChild(base)

    // 2) 炮管：圆角矩形 22×64 + 槽线 + 炮口倒角边
    const barrel = new Graphics()
    barrel.roundRect(-11, 8, 22, 64, 8).fill({ color: ART.brass, alpha: 1 })
    barrel.roundRect(-11, 8, 22, 64, 8).stroke({ width: 1, color: ART.ink500, alpha: 0.9 })
    barrel
      .moveTo(-8, 16)
      .lineTo(-8, 64)
      .moveTo(8, 16)
      .lineTo(8, 64)
      .stroke({ width: 1, color: ART.ink500, alpha: 0.85 })
    // 炮口 6px amber-400 倒角边
    barrel.roundRect(-11, 66, 22, 6, 3).fill({ color: PALETTE.amberBright, alpha: 0.95 })
    this.barrelGroup.addChild(barrel)

    // 3) 炮口晶石：菱形 10×14（amber，描边 amberBright）
    const gem = new Graphics()
    gem.poly([0, -7, 5, 0, 0, 7, -5, 0]).fill({ color: PALETTE.amber, alpha: 1 })
    gem.poly([0, -7, 5, 0, 0, 7, -5, 0]).stroke({ width: 1, color: PALETTE.amberBright, alpha: 1 })
    const gemHolder = new Container()
    gemHolder.position.set(0, 82)
    gemHolder.addChild(gem)
    this.gemCore = new Sprite({ texture: glowTexture(10, "gem") })
    this.gemCore.anchor.set(0.5)
    this.gemCore.tint = PALETTE.amberPale
    this.gemCore.alpha = 0
    this.gemCore.blendMode = "add"
    gemHolder.addChild(this.gemCore)
    this.barrelGroup.addChild(gemHolder)
    this.launcher.addChild(this.barrelGroup)

    // 4) 蓄力光环：r36 / r46 各 120° 弧，反向缓转（12s/圈）
    this.chargeRings = new Graphics()
    this.launcher.addChild(this.chargeRings)

    // 5) 刻度弧：r56 细弧 + 每 10° 4px 刻度 / 每 30° 7px 主刻度
    this.scaleArc = new Graphics()
    const R = 56
    this.scaleArc
      .arc(0, 0, R, -Math.PI / 2 - (78 * Math.PI) / 180, -Math.PI / 2 + (78 * Math.PI) / 180)
      .stroke({ width: 1, color: ART.fog400, alpha: 0.3 })
    for (let deg = -78; deg <= 78; deg += 10) {
      const a = -Math.PI / 2 + (deg * Math.PI) / 180
      const len = deg % 30 === 0 ? 7 : 4
      this.scaleArc
        .moveTo(Math.cos(a) * R, Math.sin(a) * R)
        .lineTo(Math.cos(a) * (R + len), Math.sin(a) * (R + len))
        .stroke({ width: 1, color: ART.fog400, alpha: deg % 30 === 0 ? 0.45 : 0.3 })
    }
    this.launcher.addChild(this.scaleArc)
  }

  /** 订阅引擎事件（由 StaPixiApp 在创建后绑定）。 */
  handleEngineEvent = (e: EngineEvent): void => {
    if (e.type === "launch") {
      this.flyingKind = e.ball
      this.ballKind = e.ball
      this.applyBallSkin(e.ball)
      // 动效 1：后坐 90ms + 炮口白环 r8→22 + 蓄力环增亮消散 180ms
      this.barrelRecoil = 1
      this.chargeFlash = 1
      const aim = this.engine.aimAngle
      const mx = PHYS.launchAnchor.x + Math.sin(aim) * 82
      const my = PHYS.launchAnchor.y + Math.cos(aim) * 82
      this.fx.muzzleRing(mx, my)
      this.fx.ring(mx, my, 4, 14, { width: 2, color: PALETTE.amberBright, alpha0: 0.7, maxLife: 0.12 })
    } else if (e.type === "peg-broken") {
      const resonance = e.kind === "resonance"
      this.fx.pegHitRing(e.x, e.y)
      this.fx.scorePopup(e.x, e.y, e.score, resonance)
      const color = resonance ? PALETTE.amberBright : PALETTE.jade
      if (this.flyingKind === "pierce") {
        // 穿透残影线：钉上淡金残痕 0.8s（art bible §3.7）
        const b = this.engine.ballEntity
        const vx = b ? b.body.velocity.x : 0
        const vy = b ? b.body.velocity.y : 1
        this.pierceMarks.push({
          x: e.x,
          y: e.y,
          angle: Math.atan2(vy, vx),
          life: 0.8,
        })
        this.particles.burst(e.x, e.y, PALETTE.amberPale, 3, 0.5, {
          speedMin: 20,
          speedMax: 60,
          lifeMin: 0.15,
          lifeMax: 0.25,
          sizeMin: 1.2,
          sizeMax: 2,
          gravity: 120,
        })
      } else {
        // 击钉火花 6–10 粒 + 晶体碎屑 3 块（art bible §3.7）
        this.particles.burst(e.x, e.y, PALETTE.amberPale, 8, 1, {
          speedMin: 60,
          speedMax: 190,
          lifeMin: 0.2,
          lifeMax: 0.28,
          sizeMin: 2,
          sizeMax: 4,
          gravity: 200,
        })
        this.particles.burst(e.x, e.y, color, 3, 0.8, {
          kind: "shard",
          speedMin: 40,
          speedMax: 120,
          lifeMin: 0.35,
          lifeMax: 0.5,
          sizeMin: 3,
          sizeMax: 5,
          spin: 3.14,
          gravity: 540,
        })
      }
      if (this.flyingKind === "heavy") {
        // 重弹命中：屏震 amp5 + 碎屑 6 粒 + hit-stop（art bible §3.8/动效 5）
        this.fx.shake(5)
        this.debris(e.x, e.y, resonance ? ART.brass : PALETTE.jade, 6)
        this.fx.triggerHitStop()
      }
    } else if (e.type === "obstacle-hit") {
      const ice = e.kind === "ice"
      if (e.destroyed) {
        // 击碎：石 4–6 块碎屑 / 冰 5–7 片三角薄片 + 6 粒闪光
        this.debris(e.x, e.y, ice ? PALETTE.jadeLight : ART.ink600, ice ? 6 : 5)
        if (ice) {
          this.particles.burst(e.x, e.y, ART.sparkWhite, 6, 1.2, {
            speedMin: 80,
            speedMax: 240,
            lifeMin: 0.18,
            lifeMax: 0.24,
            sizeMin: 1.5,
            sizeMax: 3,
            gravity: 80,
          })
        }
      } else {
        // 普通破损：微颤 + 少量碎屑
        const obsId = this.idAtPoint(e.x, e.y)
        if (obsId >= 0) this.obstacleTremble.set(obsId, 0.08)
        this.debris(e.x, e.y, ice ? PALETTE.jadeLight : ART.ink600, 3)
      }
      if (this.flyingKind === "heavy") {
        this.fx.shake(e.destroyed ? 5 : 3)
        this.fx.triggerHitStop()
      }
    } else if (e.type === "skill") {
      if (e.skill === "blast") {
        // 爆裂：双冲击环 + 16 火花 + 芯 + 屏震 6 + hit-stop（art bible §3.7/动效 4）
        this.fx.blastShock(e.x, e.y)
        this.particles.burst(e.x, e.y, PALETTE.amberBright, 16, 1.5, {
          speedMin: 120,
          speedMax: 320,
          lifeMin: 0.22,
          lifeMax: 0.28,
          sizeMin: 2,
          sizeMax: 4,
          gravity: 120,
        })
        this.fx.flash(0.1, 0.12)
        this.fx.shake(6)
        this.fx.triggerHitStop()
      } else if (e.skill === "pierce") {
        // 穿透：直线光痕闪（残影线在 peg-broken 分支逐钉留痕）
        const b = this.engine.ballEntity
        const vx = b ? b.body.velocity.x : 0
        const vy = b ? b.body.velocity.y : 1
        const ang = Math.atan2(vy, vx)
        this.pierceMarks.push({ x: e.x, y: e.y, angle: ang, life: 0.8 })
        this.fx.ring(e.x, e.y, 8, 26, {
          width: 2,
          color: PALETTE.amberPale,
          alpha0: 0.5,
          maxLife: 0.16,
        })
      } else {
        // 重弹：屏震 amp5 + 碎屑 + hit-stop
        this.fx.shake(5)
        this.debris(e.x, e.y, ART.brass, 6)
        this.fx.triggerHitStop()
      }
    } else if (e.type === "combo") {
      if (e.value >= 2) this.fx.comboPopup(e.value)
    } else if (e.type === "level-clear") {
      this.onLevelClear(e.stars)
    } else if (e.type === "level-fail") {
      // 收束变暗（art bible 交付 6）
      this.fx.setDim(0.5)
      this.fx.shake(4)
    }
  }

  /** 按坐标找障碍 id（微颤用；障碍数量 ≤6，线性扫足够）。 */
  private idAtPoint(x: number, y: number): number {
    for (const [id, c] of this.obstacleSprites) {
      if (Math.abs(c.position.x - x) < 80 && Math.abs(c.position.y - y) < 80) return id
    }
    return -1
  }

  private debris(x: number, y: number, color: number, count: number): void {
    this.particles.burst(x, y, color, count, 1.1, {
      kind: "shard",
      speedMin: 80,
      speedMax: 200,
      lifeMin: 0.4,
      lifeMax: 0.5,
      sizeMin: 3,
      sizeMax: 5,
      spin: 3.14, // ±180°/s
      gravity: 540, // 0.15px/步²
    })
  }

  private applyBallSkin(kind: BallKind): void {
    this.ballSprite.texture = ballTexture(kind)
    // 光晕：球径 ×2.2 预烘焙径向渐变（art bible §3.1）
    const glowTint =
      kind === "blast" ? PALETTE.amberBright : kind === "pierce" ? PALETTE.amberPale : kind === "heavy" ? ART.brass : PALETTE.amber
    this.ballGlow.tint = glowTint
    this.ballGlow.alpha = kind === "heavy" ? 0.16 : kind === "pierce" ? 0.2 : 0.25
    const glowScale = kind === "blast" ? 1.2 : kind === "pierce" ? 0.85 : 1
    this.ballGlow.scale.set(glowScale)
    this.ballSprite.scale.set(0.5, kind === "pierce" ? 0.5 : 0.5)
  }

  private onLevelClear(stars: number): void {
    // 清场收尾：剩余钉 30ms 间隔 stagger 自爆（art bible §3.7）
    let i = 0
    for (const e of this.engine.registry.all()) {
      if (!e.kind.startsWith("peg-") || !e.alive) continue
      const x = e.body.position.x
      const y = e.body.position.y
      const delay = i * 0.03
      i++
      this.pending.push({
        t: delay,
        fn: () => {
          const spr = this.pegSprites.get(e.id)
          if (spr) spr.visible = false
          this.particles.burst(x, y, PALETTE.amberPale, 6, 0.9, {
            speedMin: 40,
            speedMax: 140,
            lifeMin: 0.18,
            lifeMax: 0.2,
            sizeMin: 1.5,
            sizeMax: 3,
            gravity: 100,
          })
          this.fx.ring(x, y, 8, 20, { width: 1, color: PALETTE.amberBright, alpha0: 0.7, maxLife: 0.2 })
        },
      })
    }
    // 庆祝爆发 + 星级逐颗点亮（画布层，y≈420）+ 横向为主屏震
    this.pending.push({
      t: Math.min(0.5, i * 0.03 + 0.12),
      fn: () => {
        this.particles.burst(WIDTH / 2, HEIGHT * 0.5, PALETTE.amber, 22, 1.6, {
          speedMin: 150,
          speedMax: 380,
          lifeMin: 0.3,
          lifeMax: 0.55,
          sizeMin: 2,
          sizeMax: 4.5,
          gravity: 60,
        })
        this.particles.burst(WIDTH / 2, HEIGHT * 0.52, PALETTE.jade, 12, 1.3, {
          speedMin: 120,
          speedMax: 300,
          lifeMin: 0.3,
          lifeMax: 0.5,
          sizeMin: 2,
          sizeMax: 4,
          gravity: 60,
        })
        this.fx.starBurst(stars)
        this.fx.shake(4, true)
        this.fx.flash(0.08, 0.16)
        this.bannerAlpha = 1
      },
    })
  }

  /** 每帧由 Pixi ticker 调用。dtSec 为秒（hit-stop 时传 0）。 */
  sync(dtSec: number): void {
    this.elapsed += dtSec

    // 回关复位：level-clear/fail 是终态，UI 调 restartLevel()/nextLevel() 后 phase 回 aiming，
    // 此时清掉收束暗层/星级/横幅等残留（否则会盖到下一局）。
    const ph = this.engine.phase
    if (this.lastPhase !== ph) {
      if (ph === "aiming" && (this.lastPhase === "level-clear" || this.lastPhase === "level-fail")) {
        this.fx.setDim(0)
        this.fx.clearStars()
        this.bannerAlpha = 0
        this.clearBanner.alpha = 0
        this.pierceMarks.length = 0
      }
      this.lastPhase = ph
    }

    this.particles.update(dtSec)
    this.fx.update(dtSec)

    for (let i = this.pending.length - 1; i >= 0; i--) {
      const p = this.pending[i]
      p.t -= dtSec
      if (p.t <= 0) {
        this.pending.splice(i, 1)
        p.fn()
      }
    }

    this.syncTrajectory(dtSec)
    this.syncPegs()
    this.syncObstacles(dtSec)
    this.syncBall(dtSec)
    this.syncTrail(dtSec)
    this.syncLauncher(dtSec)

    // 残影线淡出
    for (let i = this.pierceMarks.length - 1; i >= 0; i--) {
      const m = this.pierceMarks[i]
      m.life -= dtSec
      if (m.life <= 0) this.pierceMarks.splice(i, 1)
    }

    // 屏震：只平移不旋转（art bible §3.8），作用于世界容器
    this.container.position.set(this.fx.shakeOffsetX, this.fx.shakeOffsetY)

    // CLEAR 横幅淡出
    if (this.bannerAlpha > 0) {
      this.bannerAlpha = Math.max(0, this.bannerAlpha - dtSec * 1.2)
      this.clearBanner.alpha = this.bannerAlpha
      const s = 1 + this.bannerAlpha * 0.12
      this.clearBanner.scale.set(s)
    }
  }

  // ---- 轨迹虚线（art bible §3.4） ----

  private syncTrajectory(dtSec: number): void {
    this.trajectory.clear()
    const aiming = this.engine.phase === "aiming"
    if (!aiming) {
      this.markerPop = 0
      return
    }
    const { points, firstHit } = this.engine.predictTrajectory()
    if (points.length < 2) return

    // 虚线呼吸：相位每 2s 推进 14px；reduced-motion 时停
    const phase = this.reducedMotion ? 0 : (this.elapsed * 7) % 14
    const DASH = 6
    const CYCLE = 14

    let acc = 0
    let leftover = phase // 相位偏移
    for (let i = 0; i < points.length - 1; i++) {
      const x0 = points[i].x
      const y0 = points[i].y
      const x1 = points[i + 1].x
      const y1 = points[i + 1].y
      const segLen = Math.hypot(x1 - x0, y1 - y0)
      if (segLen < 0.01) continue
      const after = firstHit >= 0 && i >= firstHit
      const alpha = after ? 0.25 : 0.55
      const ux = (x1 - x0) / segLen
      const uy = (y1 - y0) / segLen

      let d = 0
      while (d < segLen) {
        const cyclePos = (acc + d + leftover) % CYCLE
        const inDash = cyclePos < DASH
        const stepTo = Math.min(segLen - d, inDash ? DASH - cyclePos : CYCLE - cyclePos)
        if (inDash && stepTo > 0.2) {
          this.trajectory
            .moveTo(x0 + ux * d, y0 + uy * d)
            .lineTo(x0 + ux * (d + stepTo), y0 + uy * (d + stepTo))
            .stroke({ width: 2, color: PALETTE.amber, alpha })
        }
        d += stepTo
      }
      acc += segLen
      leftover = 0
    }

    // 首碰标记圈：r14 空心 + 4 刻度齿，pop 120ms scale 0.6→1
    if (firstHit >= 0 && firstHit < points.length) {
      const p = points[firstHit]
      if (Math.abs(p.x - this.lastMarkerX) > 2) {
        this.markerPop = 0
        this.lastMarkerX = p.x
      }
      this.markerPop = Math.min(1, this.markerPop + dtSec / 0.12)
      const s = 0.6 + 0.4 * easeOut(this.markerPop)
      const r = 14 * s
      this.trajectory.circle(p.x, p.y, r).stroke({ width: 1.5, color: PALETTE.amberBright, alpha: 0.95 })
      for (let k = 0; k < 4; k++) {
        const a = (k * Math.PI) / 2 + Math.PI / 4
        this.trajectory
          .moveTo(p.x + Math.cos(a) * (r - 3), p.y + Math.sin(a) * (r - 3))
          .lineTo(p.x + Math.cos(a) * r, p.y + Math.sin(a) * r)
          .stroke({ width: 1.5, color: PALETTE.amberBright, alpha: 0.9 })
      }
    }
  }

  // ---- 钉（art bible §3.2） ----

  private syncPegs(): void {
    const live = new Set<number>()
    for (const kind of ["peg-crystal", "peg-resonance"] as const) {
      for (const e of this.engine.registry.ofKind(kind)) {
        if (!e.alive) continue
        live.add(e.id)
        let spr = this.pegSprites.get(e.id)
        if (!spr) {
          spr = new Sprite({ texture: pegTexture(kind === "peg-resonance") })
          spr.anchor.set(0.5)
          const big = (e.hp ?? 1) >= 2
          const baseScale = PHYS.pegRadius / 22
          spr.scale.set(baseScale * (big ? 1.35 : 1))
          spr.position.set(e.body.position.x, e.body.position.y)
          this.pegLayer.addChild(spr)
          this.pegSprites.set(e.id, spr)
        }
        // hp=2 大钉：外圈加一环
        // 破损态（hp 下降）：裂纹由 pegFlashG 逐帧补画
        const maxHp = this.maxHpOf(e)
        if (e.hp < maxHp) {
          spr.tint = 0xb8b8b8
        } else {
          spr.tint = 0xffffff
        }
      }
    }
    for (const [id, spr] of this.pegSprites) {
      if (!live.has(id)) {
        spr.destroy()
        this.pegSprites.delete(id)
        this.maxHpCache.delete(id)
      }
    }
    this.redrawPegFx()
  }

  private maxHpCache = new Map<number, number>()

  private maxHpOf(e: Entity): number {
    let m = this.maxHpCache.get(e.id)
    if (m === undefined) {
      m = e.hp
      this.maxHpCache.set(e.id, m)
    }
    return m
  }

  /** 钉层叠加：破损裂纹 + 穿透残影线 + 共鸣钉呼吸环（唯一常驻循环动效，art bible §3.2）。 */
  private redrawPegFx(): void {
    this.pegFlashG.clear()
    for (const e of this.engine.registry.all()) {
      if (!e.kind.startsWith("peg-") || !e.alive) continue
      const x = e.body.position.x
      const y = e.body.position.y
      const r = PHYS.pegRadius

      // 共鸣呼吸环：r 12→16，2.6s 循环，alpha 30%→8%
      if (e.kind === "peg-resonance") {
        const ph = ((this.elapsed / 2.6 + (e.id % 17) / 17) % 1 + 1) % 1
        const wave = 0.5 - 0.5 * Math.cos(ph * Math.PI * 2)
        const rr = 12 + 4 * wave
        this.pegFlashG
          .circle(x, y, rr)
          .stroke({ width: 1, color: PALETTE.amber, alpha: 0.3 - 0.22 * wave })
      }

      // 破损裂纹（hp 下降后）
      const maxHp = this.maxHpOf(e)
      if (e.hp < maxHp) {
        this.pegFlashG
          .moveTo(x - r * 0.6, y - r * 0.3)
          .lineTo(x + r * 0.1, y + r * 0.15)
          .lineTo(x + r * 0.55, y - r * 0.1)
          .stroke({ width: 1, color: ART.fog400, alpha: 0.55 })
        this.pegFlashG
          .moveTo(x - r * 0.2, y + r * 0.55)
          .lineTo(x + r * 0.15, y + r * 0.05)
          .stroke({ width: 1, color: ART.fog400, alpha: 0.45 })
      }
    }
    // 穿透残影线（24×2 @35%，0.8s 线性淡出）
    for (const m of this.pierceMarks) {
      const a = (m.life / 0.8) * 0.35
      const dx = Math.cos(m.angle) * 12
      const dy = Math.sin(m.angle) * 12
      this.pegFlashG
        .moveTo(m.x - dx, m.y - dy)
        .lineTo(m.x + dx, m.y + dy)
        .stroke({ width: 2, color: PALETTE.amberPale, alpha: a })
    }
  }

  // ---- 障碍（art bible §3.3） ----

  private syncObstacles(dtSec: number): void {
    const live = new Set<number>()
    for (const kind of ["obstacle-stone", "obstacle-ice"] as const) {
      for (const e of this.engine.registry.ofKind(kind)) {
        if (!e.alive) continue
        live.add(e.id)
        const existing = this.obstacleSprites.get(e.id)
        const lastHp = this.obstacleHp.get(e.id)
        if (!existing || lastHp !== e.hp) {
          // 首次生成，或 hp 下降（裂纹破损态）→ 重建图形
          existing?.destroy({ children: true })
          const c = this.buildObstacle(e, kind === "obstacle-ice")
          c.position.set(e.body.position.x, e.body.position.y)
          this.obstacleLayer.addChild(c)
          this.obstacleSprites.set(e.id, c)
          this.obstacleHp.set(e.id, e.hp)
        }
      }
    }
    for (const [id, c] of this.obstacleSprites) {
      if (!live.has(id)) {
        c.destroy({ children: true })
        this.obstacleSprites.delete(id)
        this.obstacleHp.delete(id)
        this.obstacleTremble.delete(id)
      }
    }
    // 微颤衰减（普通球打不动：0.3px / 80ms）
    for (const [id, t] of this.obstacleTremble) {
      const nt = t - dtSec
      const c = this.obstacleSprites.get(id)
      if (!c || nt <= 0) {
        if (c) {
          const e = this.findObs(id)
          if (e) c.position.set(e.body.position.x, e.body.position.y)
        }
        this.obstacleTremble.delete(id)
        continue
      }
      this.obstacleTremble.set(id, nt)
      const e = this.findObs(id)
      if (e) {
        const amp = 0.3 * (nt / 0.08)
        c.position.set(
          e.body.position.x + (Math.random() * 2 - 1) * amp,
          e.body.position.y + (Math.random() * 2 - 1) * amp,
        )
      }
    }
  }

  private findObs(id: number): Entity | undefined {
    for (const e of this.engine.registry.all()) if (e.id === id) return e
    return undefined
  }

  /** 不规则多边形障碍（双面切色 + 缺口 + 裂纹破损态）。 */
  private buildObstacle(e: Entity, ice: boolean): Container {
    const w = (e.meta?.w as number) ?? 40
    const h = (e.meta?.h as number) ?? 40
    const c = new Container()
    const g = new Graphics()

    // 顶点：8 边不规则（确定性 jitter，按 id 播种）
    const verts: Array<[number, number]> = []
    const n = 8
    let seed = (e.id * 2654435761) >>> 0
    const rnd = () => {
      seed = (seed + 0x6d2b79f5) | 0
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296
    }
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2 + (rnd() - 0.5) * 0.25
      const rx = (w / 2) * (0.86 + rnd() * 0.18)
      const ry = (h / 2) * (0.86 + rnd() * 0.18)
      verts.push([Math.cos(a) * rx, Math.sin(a) * ry])
    }

    const poly = (pts: Array<[number, number]>) => pts.flatMap(([x, y]) => [x, y])
    if (ice) {
      // 冰：fog-100 @22% + jadeLight @18%，描边 jadeLight @60%
      g.poly(poly(verts)).fill({ color: ART.fog100, alpha: 0.22 })
      g.poly(poly(verts.map(([x, y]) => [x * 0.92, y * 0.92] as [number, number]))).fill({
        color: PALETTE.jadeLight,
        alpha: 0.18,
      })
      g.poly(poly(verts)).stroke({ width: 1, color: PALETTE.jadeLight, alpha: 0.6 })
      // 内部折射线 2–3 条
      for (let i = 0; i < 3; i++) {
        const x0 = -w * 0.3 + i * w * 0.3
        g.moveTo(x0, -h * 0.42)
          .lineTo(x0 + w * 0.12, h * 0.42)
          .stroke({ width: 1, color: ART.sparkWhite, alpha: 0.12 })
      }
    } else {
      // 石：主面 ink-600 / 背光面 ink-500，边缘断续缺口
      g.poly(poly(verts)).fill({ color: ART.ink600, alpha: 1 })
      // 背光面：右下半
      const half = verts.map(([x, y], i) =>
        i <= 4 ? [x, y] as [number, number] : [x * 0.55, y * 0.55] as [number, number],
      )
      g.poly(poly(half)).fill({ color: ART.ink500, alpha: 1 })
      // 3–4 处小缺口（断续描边）
      for (let i = 0; i < n; i++) {
        if (i % 3 === 1) continue
        const [x0, y0] = verts[i]
        const [x1, y1] = verts[(i + 1) % n]
        g.moveTo(x0, y0)
          .lineTo(x0 + (x1 - x0) * 0.72, y0 + (y1 - y0) * 0.72)
          .stroke({ width: 1, color: ART.fog400, alpha: 0.55 })
      }
    }

    // 破损态裂纹（hp 下降时）
    const maxHp = this.maxHpOf(e)
    if (e.hp < maxHp) {
      const crackColor = ice ? ART.sparkWhite : ART.fog400
      const crackAlpha = ice ? 0.35 : 0.4
      g.moveTo(-w * 0.35, -h * 0.3)
        .lineTo(0, h * 0.05)
        .lineTo(w * 0.3, -h * 0.15)
        .stroke({ width: 1, color: crackColor, alpha: crackAlpha })
      g.moveTo(-w * 0.15, h * 0.35)
        .lineTo(w * 0.1, h * 0.05)
        .stroke({ width: 1, color: crackColor, alpha: crackAlpha * 0.85 })
    }

    c.addChild(g)
    return c
  }

  // ---- 球（art bible §3.1 四球种） ----

  private syncBall(dtSec: number): void {
    const ball = this.engine.ballEntity
    if (!ball) {
      this.ballSprite.visible = false
      this.ballGlow.visible = false
      return
    }
    // 瞄准期球种 = 队列首（selectBall 换位后 meta 不更新，取 hudSnapshot 的 currentBall）
    if (this.engine.phase === "aiming") {
      const k = this.engine.hudSnapshot().currentBall ?? "standard"
      if (k !== this.ballKind) {
        this.ballKind = k
        this.applyBallSkin(k)
      }
    } else if (this.flyingKind && this.flyingKind !== this.ballKind) {
      this.ballKind = this.flyingKind
      this.applyBallSkin(this.flyingKind)
    }

    const x = ball.body.position.x
    const y = ball.body.position.y
    this.ballSprite.position.set(x, y)
    this.ballGlow.position.set(x, y)
    this.ballSprite.visible = true
    this.ballGlow.visible = true

    // 重弹：每 3 步掉 1 粒重尘（寿命 300ms 垂直下落）
    if (this.engine.phase === "flying" && this.ballKind === "heavy" && dtSec > 0) {
      this.heavyStep += dtSec * 60
      if (this.heavyStep >= 3) {
        this.heavyStep = 0
        this.particles.burst(x, y + PHYS.ballRadius, ART.brass, 1, 0.3, {
          speedMin: 5,
          speedMax: 25,
          upBias: -30,
          lifeMin: 0.3,
          lifeMax: 0.3,
          sizeMin: 1.2,
          sizeMax: 2,
          gravity: 400,
        })
      }
    }
  }

  private syncTrail(dtSec: number): void {
    this.trailG.clear()
    const ball = this.engine.ballEntity
    const flying = this.engine.phase === "flying" && ball

    if (flying && dtSec > 0) {
      const x = ball.body.position.x
      const y = ball.body.position.y
      // 只在位移 >0.8px 时入环，避免原地堆点
      const h = this.trailHead
      const last = this.trailCount > 0 ? (h - 1 + TRAIL_CAP) % TRAIL_CAP : -1
      if (last < 0 || Math.hypot(x - this.trailX[last], y - this.trailY[last]) > 0.8) {
        this.trailX[h] = x
        this.trailY[h] = y
        this.trailT[h] = this.elapsed
        this.trailHead = (h + 1) % TRAIL_CAP
        if (this.trailCount < TRAIL_CAP) this.trailCount++
      }
    } else if (this.trailCount > 0 && !flying) {
      this.trailCount = 0
      this.trailHead = 0
    }

    if (this.trailCount < 2) return

    if (this.ballKind === "pierce") {
      // 残影线：沿速度方向 24px 拉长线段（amberPale @40%，宽 3px），不掉点
      const b = ball!
      const vx = b.body.velocity.x
      const vy = b.body.velocity.y
      const sp = Math.hypot(vx, vy) || 1
      const x = b.body.position.x
      const y = b.body.position.y
      this.trailG
        .moveTo(x - (vx / sp) * 24, y - (vy / sp) * 24)
        .lineTo(x, y)
        .stroke({ width: 3, color: PALETTE.amberPale, alpha: 0.4 })
      return
    }

    if (this.ballKind === "heavy") return // 无拖尾

    // standard / blast：8 点渐隐残影，间距 6px，寿命 140ms
    const LIFE = 0.14
    const SPACING = 6
    let placed = 0
    let refX = 0
    let refY = 0
    let haveRef = false
    for (let i = 1; i <= this.trailCount && placed < 8; i++) {
      const idx = (this.trailHead - i + TRAIL_CAP * 2) % TRAIL_CAP
      const age = this.elapsed - this.trailT[idx]
      if (age > LIFE) break
      const px = this.trailX[idx]
      const py = this.trailY[idx]
      if (haveRef && Math.hypot(px - refX, py - refY) < SPACING) continue
      refX = px
      refY = py
      haveRef = true
      const t = 1 - age / LIFE
      const alpha = 0.5 * t
      const r = PHYS.ballRadius * (0.45 + t * 0.35)
      this.trailG.circle(px, py, r).fill({
        color: this.ballKind === "blast" ? PALETTE.amberBright : PALETTE.amber,
        alpha,
      })
      placed++
      // blast 拖尾尾端 2–3 粒火星（寿命 200ms）
      if (this.ballKind === "blast" && placed >= 6 && dtSec > 0 && Math.random() < 0.35) {
        this.particles.burst(px, py, PALETTE.amberPale, 1, 0.35, {
          speedMin: 10,
          speedMax: 50,
          lifeMin: 0.2,
          lifeMax: 0.2,
          sizeMin: 1,
          sizeMax: 2,
          gravity: 60,
        })
      }
    }
  }

  // ---- 发射器每帧（蓄力环/晶石/后坐） ----

  private syncLauncher(dtSec: number): void {
    this.barrelGroup.rotation = -this.engine.aimAngle

    // 后坐 4px 复位（90ms easeOut）
    if (this.barrelRecoil > 0) {
      this.barrelRecoil = Math.max(0, this.barrelRecoil - dtSec / 0.09)
      const off = -4 * this.barrelRecoil
      this.barrelGroup.position.set(0, off)
    }

    // 蓄力环：r36/r46 各 120° 弧反向缓转；发射瞬间增亮 180ms 消散
    this.chargeRings.clear()
    const aiming = this.engine.phase === "aiming"
    const rot = this.reducedMotion ? 0 : this.elapsed * ((Math.PI * 2) / 12)
    const flash = this.chargeFlash
    if (flash > 0) this.chargeFlash = Math.max(0, flash - dtSec / 0.18)
    const baseAlpha = aiming ? 0.55 : 0.25
    const color = flash > 0.05 ? PALETTE.amberBright : PALETTE.amber
    const arcAlpha = baseAlpha + flash * 0.45
    for (const [r, dir] of [
      [36, 1],
      [46, -1],
    ] as const) {
      const start = rot * dir
      this.chargeRings
        .arc(0, 0, r, start, start + (Math.PI * 2) / 3)
        .stroke({ width: 2, color, alpha: arcAlpha })
    }

    // 炮口晶石：蓄力（瞄准）时内芯变 amberPale
    this.gemCore.alpha = aiming ? 0.5 + 0.2 * Math.sin(this.elapsed * 2.2) : 0
  }

  destroy(): void {
    this.container.destroy({ children: true })
    this.overlay.destroy({ children: true })
  }

  /**
   * hit-stop（命中停顿）：返回本帧是否应冻结画面。
   * 由 StaPixiApp 据此跳过引擎 tick 与本层 sync —— 停顿作用于世界时钟，引擎零改动。
   */
  consumeHitStop(dtMs: number): boolean {
    return this.fx.consumeHitStop(dtMs)
  }
}
