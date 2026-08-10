import { Container, Graphics } from "pixi.js"

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  life: number
  maxLife: number
  size: number
  color: number
  active: boolean
}

/**
 * 轻量粒子系统（Stage Spec §6.6 钉破碎碎片 / 爆炸）。
 * 对象池复用，单 Graphics 每帧重绘（v8 批量 fill，碎片量级无压力）。
 */
export class ParticleSystem {
  readonly container = new Container()

  private pool: Particle[] = []
  private graphics = new Graphics()
  private gravityPerSec = 0.25 * 60 // 碎片微重力

  constructor() {
    this.container.addChild(this.graphics)
  }

  private obtain(): Particle {
    let p = this.pool.find((q) => !q.active)
    if (!p) {
      p = { x: 0, y: 0, vx: 0, vy: 0, life: 0, maxLife: 1, size: 2, color: 0xffffff, active: false }
      this.pool.push(p)
    }
    return p
  }

  /** 在 (x,y) 爆发 count 个 color 碎片。 */
  burst(x: number, y: number, color: number, count = 8, power = 1): void {
    for (let i = 0; i < count; i++) {
      const p = this.obtain()
      const a = Math.random() * Math.PI * 2
      const sp = (1 + Math.random() * 3) * power
      p.x = x
      p.y = y
      p.vx = Math.cos(a) * sp
      p.vy = Math.sin(a) * sp - 1.2 * power
      p.maxLife = 0.5 + Math.random() * 0.45
      p.life = p.maxLife
      p.size = 1.5 + Math.random() * 2.2
      p.color = color
      p.active = true
    }
  }

  update(dtSec: number): void {
    for (const p of this.pool) {
      if (!p.active) continue
      p.life -= dtSec
      if (p.life <= 0) {
        p.active = false
        continue
      }
      p.vy += this.gravityPerSec * dtSec
      p.x += p.vx * 60 * dtSec
      p.y += p.vy * 60 * dtSec
    }
    this.redraw()
  }

  private redraw(): void {
    this.graphics.clear()
    for (const p of this.pool) {
      if (!p.active) continue
      const a = Math.max(0, p.life / p.maxLife)
      this.graphics.circle(p.x, p.y, p.size).fill({ color: p.color, alpha: a })
    }
  }

  destroy(): void {
    this.container.destroy({ children: true })
  }
}
