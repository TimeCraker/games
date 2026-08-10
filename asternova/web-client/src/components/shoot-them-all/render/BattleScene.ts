import { Container, Graphics } from "pixi.js"

import { PALETTE, PHYS } from "../constants"
import type { GameEngine } from "../engine/GameEngine"

/** 画一颗普通晶体（Azurite 六边形，半透 + 高光内核）。M1 基础几何。 */
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
 * 战斗场景渲染层（Stage Spec §8.7，Pixi 侧）。
 * 每帧从 GameEngine 同步：钉子增删、球位置、发射器瞄准方向。只画不持逻辑。
 */
export class BattleScene {
  readonly container = new Container()

  private pegLayer = new Container()
  private ballLayer = new Container()
  private launcher = new Container()
  private launcherBarrel: Graphics
  private pegSprites = new Map<number, Graphics>()
  private ballSprite: Graphics | null = null

  constructor(private readonly engine: GameEngine) {
    this.container.addChild(this.pegLayer)
    this.container.addChild(this.ballLayer)
    this.container.addChild(this.launcher)
    this.launcher.position.set(PHYS.launchAnchor.x, PHYS.launchAnchor.y)
    this.launcher.addChild(this.paintLauncherBase())
    this.launcherBarrel = this.paintLauncherBarrel()
    this.launcher.addChild(this.launcherBarrel)
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
    // 默认指向 +y（下），由 rotation = -aimAngle 旋转到瞄准方向
    g.moveTo(0, 4).lineTo(0, 30).stroke({ width: 3, color: PALETTE.azurite, alpha: 0.9 })
    g.moveTo(0, 30).lineTo(-4, 24).moveTo(0, 30).lineTo(4, 24).stroke({
      width: 2,
      color: PALETTE.azurite,
      alpha: 0.8,
    })
    return g
  }

  /** 每帧由 Pixi ticker 调用，同步引擎状态到 sprite。 */
  sync(): void {
    this.syncPegs()
    this.syncBall()
    this.launcherBarrel.rotation = -this.engine.aimAngle
  }

  private syncPegs(): void {
    const live = new Set<number>()
    for (const e of this.engine.registry.ofKind("peg-crystal")) {
      if (!e.alive) continue
      live.add(e.id)
      let g = this.pegSprites.get(e.id)
      if (!g) {
        g = new Graphics()
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

  destroy(): void {
    this.container.destroy({ children: true })
  }
}
