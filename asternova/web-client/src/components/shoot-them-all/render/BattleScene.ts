import { Container, Graphics, Text } from "pixi.js"

import { HEIGHT, PALETTE, PHYS, WIDTH } from "../constants"
import type { EngineEvent, GameEngine } from "../engine/GameEngine"
import { ParticleSystem } from "./ParticleSystem"

/** 画一颗钉（晶体=翠玉六边形 / 共鸣=琥珀六边形+内核更亮）。 */
function paintCrystal(g: Graphics, resonance = false): void {
  const r = PHYS.pegRadius
  const pts = [0, -r * 1.15, r, -r * 0.55, r, r * 0.55, 0, r * 1.15, -r, r * 0.55, -r, -r * 0.55]
  const base = resonance ? PALETTE.amberBright : PALETTE.jade
  const line = resonance ? PALETTE.amberPale : PALETTE.jadeLight
  g.poly(pts).fill({ color: base, alpha: 0.5 })
  g.poly(pts).stroke({ width: 1.3, color: line, alpha: 0.85 })
  g.circle(0, -r * 0.2, r * 0.32).fill({ color: 0xffffff, alpha: resonance ? 0.7 : 0.5 })
}

/** 画一块障碍（stone=冷灰石板 / ice=半透冰板）。最小适配版，美术细节留给后续波次。 */
function paintObstacle(g: Graphics, w: number, h: number, ice: boolean): void {
  g.rect(-w / 2, -h / 2, w, h)
  g.fill({ color: ice ? PALETTE.jadeLight : PALETTE.line, alpha: ice ? 0.28 : 0.45 })
  g.rect(-w / 2, -h / 2, w, h).stroke({
    width: 1.6,
    color: ice ? PALETTE.jadeLight : PALETTE.line,
    alpha: 0.9,
  })
}

/** 画陨星（Azurite 球 + 外辉光 + 高光）。 */
function paintBall(g: Graphics): void {
  const r = PHYS.ballRadius
  g.circle(0, 0, r * 1.85).fill({ color: PALETTE.amber, alpha: 0.18 })
  g.circle(0, 0, r).fill({ color: PALETTE.amber, alpha: 0.95 })
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
    } else if (e.type === "level-clear") {
      this.particles.burst(WIDTH / 2, HEIGHT * 0.55, PALETTE.amber, 22, 1.6)
      this.particles.burst(WIDTH / 2, HEIGHT * 0.45, PALETTE.jade, 18, 1.4)
      this.shake(6)
      this.showToast(`过关 · ${"★".repeat(e.stars)}${"☆".repeat(3 - e.stars)}`)
    } else if (e.type === "level-fail") {
      this.shake(4)
      this.showToast("未达标 · LEVEL FAIL")
    } else if (e.type === "skill") {
      // 球种技能闪光：爆裂/穿透/重击的共同反馈锚点
      const color = e.skill === "blast" ? PALETTE.danger : e.skill === "pierce" ? PALETTE.jadeLight : PALETTE.amberBright
      this.particles.burst(e.x, e.y, color, 16, 1.5)
      this.shake(3)
    } else if (e.type === "obstacle-hit" && e.destroyed) {
      this.particles.burst(e.x, e.y, PALETTE.line, 12, 1.2)
      this.shake(2.4)
    } else if (e.type === "launch") {
      this.shake(0.8)
    }
  }

  private colorForKind(kind: string): number {
    return kind === "crystal" ? PALETTE.jade : kind === "resonance" ? PALETTE.amberBright : PALETTE.danger
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
      this.trajectory.circle(p.x, p.y, after ? 1.8 : 2.4).fill({ color: 0xf2d79b, alpha })
    }
    if (firstHit >= 0 && firstHit < points.length) {
      const p = points[firstHit]
      this.trajectory.circle(p.x, p.y, 9).stroke({ width: 1.5, color: PALETTE.amber, alpha: 0.9 })
      this.trajectory.circle(p.x, p.y, 4.5).fill({ color: PALETTE.amber, alpha: 0.5 })
    }
  }

  private syncPegs(): void {
    const live = new Set<number>()
    // 关卡制板面上有 crystal/resonance 钉 + stone/ice 障碍，全部同步（最小适配版：
    // 每种一个静态画法，视觉精雕留给后续美术波次）
    for (const kind of ["peg-crystal", "peg-resonance", "obstacle-stone", "obstacle-ice"] as const) {
      for (const e of this.engine.registry.ofKind(kind)) {
        if (!e.alive) continue
        live.add(e.id)
        if (!this.pegSprites.has(e.id)) {
          const g = new Graphics()
          if (kind.startsWith("obstacle-")) paintObstacle(g, e.meta?.w as number, e.meta?.h as number, kind === "obstacle-ice")
          else paintCrystal(g, kind === "peg-resonance")
          g.position.set(e.body.position.x, e.body.position.y)
          this.pegLayer.addChild(g)
          this.pegSprites.set(e.id, g)
        }
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
          .fill({ color: PALETTE.amberBright, alpha: 0.06 + t * 0.22 })
      }
    } else if (this.trail.length) {
      this.trail.length = 0
    }
  }

  private paintLauncherBase(): Graphics {
    const g = new Graphics()
    g.circle(0, 0, 16).fill({ color: 0x111316, alpha: 0.85 })
    g.circle(0, 0, 16).stroke({ width: 1.6, color: PALETTE.amber, alpha: 0.8 })
    g.circle(0, 0, 6).fill({ color: PALETTE.amber, alpha: 0.95 })
    return g
  }

  private paintLauncherBarrel(): Graphics {
    const g = new Graphics()
    g.moveTo(0, 4).lineTo(0, 30).stroke({ width: 3, color: PALETTE.amber, alpha: 0.9 })
    g
      .moveTo(0, 30)
      .lineTo(-4, 24)
      .moveTo(0, 30)
      .lineTo(4, 24)
      .stroke({ width: 2, color: PALETTE.amber, alpha: 0.8 })
    return g
  }

  destroy(): void {
    this.container.destroy({ children: true })
  }
}
