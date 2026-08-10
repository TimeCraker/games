import { Container, Graphics, Text } from "pixi.js"

import { HEIGHT, PALETTE, PHYS, WIDTH } from "../constants"
import type { EngineEvent, GameEngine } from "../engine/GameEngine"
import { ParticleSystem } from "./ParticleSystem"

/** 画一颗普通晶体（Azurite 六边形，半透 + 高光内核）。 */
function paintCrystal(g: Graphics): void {
  const r = PHYS.pegRadius
  const pts = [0, -r * 1.15, r, -r * 0.55, r, r * 0.55, 0, r * 1.15, -r, r * 0.55, -r, -r * 0.55]
  g.poly(pts).fill({ color: PALETTE.azurite, alpha: 0.5 })
  g.poly(pts).stroke({ width: 1.3, color: 0xc7ecff, alpha: 0.85 })
  g.circle(0, -r * 0.2, r * 0.32).fill({ color: 0xffffff, alpha: 0.5 })
}

/** 画陨星（Azurite 球 + 外辉光 + 高光）。 */
function paintBall(g: Graphics): void {
  const r = PHYS.ballRadius
  g.circle(0, 0, r * 1.85).fill({ color: PALETTE.azurite, alpha: 0.18 })
  g.circle(0, 0, r).fill({ color: PALETTE.azurite, alpha: 0.95 })
  g.circle(0, 0, r).stroke({ width: 1.2, color: 0xffffff, alpha: 0.9 })
  g.circle(-r * 0.3, -r * 0.35, r * 0.32).fill({ color: 0xffffff, alpha: 0.85 })
}

/**
 * 战斗场景渲染层（Stage Spec §8.7）。每帧从 GameEngine 同步 + 驱动 Juice。
 * 订阅 engine.onEvent 触发粒子/屏震/Toast（引擎层零 Pixi，靠回调通知）。
 */
export class BattleScene {
  readonly container = new Container()

  private pegLayer = new Container()
  private trajectory = new Graphics()
  private particles = new ParticleSystem()
  private trailGraphics = new Graphics()
  private ballLayer = new Container()
  private launcher = new Container()
  private launcherBarrel: Graphics
  private toast: Text

  private pegSprites = new Map<number, Graphics>()
  private ballSprite: Graphics | null = null
  private trail: Array<{ x: number; y: number }> = []

  private shakeMag = 0
  private toastAlpha = 0

  constructor(private readonly engine: GameEngine) {
    this.container.addChild(this.pegLayer)
    this.container.addChild(this.trajectory)
    this.container.addChild(this.particles.container)
    this.container.addChild(this.trailGraphics)
    this.container.addChild(this.ballLayer)
    this.container.addChild(this.launcher)

    this.launcher.position.set(PHYS.launchAnchor.x, PHYS.launchAnchor.y)
    this.launcher.addChild(this.paintLauncherBase())
    this.launcherBarrel = this.paintLauncherBarrel()
    this.launcher.addChild(this.launcherBarrel)

    this.toast = new Text({
      text: "",
      style: {
        fontFamily: "Orbitron, 'PingFang SC', sans-serif",
        fontSize: 34,
        fontWeight: "bold",
        fill: 0xffffff,
        stroke: { color: PALETTE.amber, width: 3 },
        letterSpacing: 3,
      },
    })
    this.toast.anchor.set(0.5)
    this.toast.position.set(WIDTH / 2, HEIGHT * 0.38)
    this.toast.alpha = 0
    this.container.addChild(this.toast)
  }

  /** 订阅引擎事件（由 StaPixiApp 在创建后绑定）。 */
  handleEngineEvent = (e: EngineEvent): void => {
    if (e.type === "peg-broken") {
      this.particles.burst(e.x, e.y, this.colorForKind(e.kind), 7)
      this.shake(1.6)
    } else if (e.type === "node-clear") {
      this.particles.burst(e.x, e.y, PALETTE.amber, 22, 1.6)
      this.particles.burst(WIDTH / 2, HEIGHT * 0.55, PALETTE.azurite, 18, 1.4)
      this.shake(6)
      this.showToast("节点清空 · NODE CLEAR")
    } else if (e.type === "launch") {
      this.shake(0.8)
    }
  }

  private colorForKind(kind: string): number {
    return kind === "peg-crystal" ? PALETTE.azurite : PALETTE.amber
  }

  private showToast(text: string): void {
    this.toast.text = text
    this.toastAlpha = 1
    this.toast.scale.set(1.25)
  }

  private shake(mag: number): void {
    this.shakeMag = Math.min(8, Math.max(this.shakeMag, mag))
  }

  /** 每帧由 Pixi ticker 调用。dtSec 为秒。 */
  sync(dtSec: number): void {
    this.particles.update(dtSec)
    this.syncTrajectory()
    this.syncPegs()
    this.syncBall()
    this.syncTrail()
    this.launcherBarrel.rotation = -this.engine.aimAngle

    // 屏震衰减（帧率无关）+ 应用
    if (this.shakeMag > 0.1) {
      this.shakeMag *= Math.pow(0.85, dtSec * 60)
      this.container.position.set(
        (Math.random() * 2 - 1) * this.shakeMag,
        (Math.random() * 2 - 1) * this.shakeMag,
      )
    } else {
      this.shakeMag = 0
      this.container.position.set(0, 0)
    }

    // Toast 淡出 + 缩放回弹
    if (this.toastAlpha > 0) {
      this.toastAlpha = Math.max(0, this.toastAlpha - dtSec * 0.9)
      this.toast.alpha = this.toastAlpha
      const s = this.toast.scale.x + (1 - this.toast.scale.x) * Math.min(1, dtSec * 8)
      this.toast.scale.set(s)
    }
  }

  private syncTrajectory(): void {
    this.trajectory.clear()
    if (this.engine.phase !== "aiming") return
    const { points, firstHit } = this.engine.predictTrajectory()
    if (points.length === 0) return
    for (let i = 0; i < points.length; i++) {
      const p = points[i]
      const after = firstHit >= 0 && i > firstHit
      const alpha = after
        ? Math.max(0.06, 0.3 - (i - firstHit) * 0.02)
        : Math.max(0.12, 0.5 - (i / Math.max(1, points.length - 1)) * 0.3)
      this.trajectory.circle(p.x, p.y, after ? 1.8 : 2.4).fill({ color: 0xc7ecff, alpha })
    }
    if (firstHit >= 0 && firstHit < points.length) {
      const p = points[firstHit]
      this.trajectory.circle(p.x, p.y, 9).stroke({ width: 1.5, color: PALETTE.amber, alpha: 0.9 })
      this.trajectory.circle(p.x, p.y, 4.5).fill({ color: PALETTE.amber, alpha: 0.5 })
    }
  }

  private syncPegs(): void {
    const live = new Set<number>()
    for (const e of this.engine.registry.ofKind("peg-crystal")) {
      if (!e.alive) continue
      live.add(e.id)
      if (!this.pegSprites.has(e.id)) {
        const g = new Graphics()
        paintCrystal(g)
        g.position.set(e.body.position.x, e.body.position.y)
        this.pegLayer.addChild(g)
        this.pegSprites.set(e.id, g)
      }
    }
    for (const [id, g] of this.pegSprites) {
      if (!live.has(id)) {
        g.destroy()
        this.pegSprites.delete(id)
      }
    }
  }

  private syncBall(): void {
    const ball = this.engine.ballEntity
    if (!ball) {
      if (this.ballSprite) this.ballSprite.visible = false
      return
    }
    if (!this.ballSprite) {
      const g = new Graphics()
      paintBall(g)
      this.ballLayer.addChild(g)
      this.ballSprite = g
    }
    this.ballSprite.position.set(ball.body.position.x, ball.body.position.y)
    this.ballSprite.visible = true
  }

  private syncTrail(): void {
    this.trailGraphics.clear()
    const ball = this.engine.ballEntity
    if (this.engine.phase === "flying" && ball) {
      this.trail.push({ x: ball.body.position.x, y: ball.body.position.y })
      if (this.trail.length > 16) this.trail.shift()
      for (let i = 0; i < this.trail.length; i++) {
        const p = this.trail[i]
        const t = i / Math.max(1, this.trail.length - 1)
        this.trailGraphics
          .circle(p.x, p.y, 1.4 + t * 2.4)
          .fill({ color: PALETTE.azurite, alpha: 0.06 + t * 0.22 })
      }
    } else if (this.trail.length) {
      this.trail.length = 0
    }
  }

  private paintLauncherBase(): Graphics {
    const g = new Graphics()
    g.circle(0, 0, 16).fill({ color: 0x0e1130, alpha: 0.85 })
    g.circle(0, 0, 16).stroke({ width: 1.6, color: PALETTE.azurite, alpha: 0.8 })
    g.circle(0, 0, 6).fill({ color: PALETTE.azurite, alpha: 0.95 })
    return g
  }

  private paintLauncherBarrel(): Graphics {
    const g = new Graphics()
    g.moveTo(0, 4).lineTo(0, 30).stroke({ width: 3, color: PALETTE.azurite, alpha: 0.9 })
    g
      .moveTo(0, 30)
      .lineTo(-4, 24)
      .moveTo(0, 30)
      .lineTo(4, 24)
      .stroke({ width: 2, color: PALETTE.azurite, alpha: 0.8 })
    return g
  }

  destroy(): void {
    this.container.destroy({ children: true })
  }
}
