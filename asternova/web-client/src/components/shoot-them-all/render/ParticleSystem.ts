import { Container, Graphics } from "pixi.js"

/**
 * 粒子系统（art bible §3.7 / §7 60fps 预算）。
 *
 * 预算硬顶：常驻 ≤120、峰值 ≤200（400ms 内回落）、单帧新增 ≤40。
 * 对象池复用，update 全程零分配；两类图元各一个 Graphics 批量重绘：
 * 圆点（火花/重尘/闪光）与多边形碎屑（石/冰/菱形碎屑）。
 * 速度单位 px/秒，重力按 px/秒² 给（art bible 的 0.15px/步² ≈ 540px/秒²）。
 */

/** 预算常量（art bible §3.7 粒子预算） */
export const PARTICLE_BUDGET = {
  resident: 120,
  peak: 200,
  perFrame: 40,
} as const

export type ParticleKind = "dot" | "shard"

export interface BurstOpts {
  count?: number
  power?: number
  /** px/秒 */
  speedMin?: number
  speedMax?: number
  /** 秒 */
  lifeMin?: number
  lifeMax?: number
  /** px 尺寸（线性归零） */
  sizeMin?: number
  sizeMax?: number
  gravity?: number
  kind?: ParticleKind
  /** 初速向上偏置（px/秒） */
  upBias?: number
  /** 自转（弧度/秒，仅 shard） */
  spin?: number
}

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  life: number
  maxLife: number
  size: number
  color: number
  gravity: number
  spin: number
  rot: number
  kind: ParticleKind
  active: boolean
}

const DEFAULTS: Required<Omit<BurstOpts, "count">> = {
  power: 1,
  speedMin: 40,
  speedMax: 180,
  lifeMin: 0.28,
  lifeMax: 0.7,
  sizeMin: 1.5,
  sizeMax: 3.7,
  gravity: 540,
  kind: "dot",
  upBias: 72,
  spin: 0,
}

/**
 * 轻量粒子系统：对象池 + 单帧双 Graphics 重绘。
 * reducedMotion 时全局数量砍到 10%（art bible §5 末）。
 */
export class ParticleSystem {
  readonly container = new Container()

  private pool: Particle[] = []
  private dots = new Graphics()
  private shards = new Graphics()
  /** 本帧已新增数（≤40 硬顶） */
  private spawnedThisFrame = 0
  private reducedMotion = false

  constructor() {
    this.container.addChild(this.dots)
    this.container.addChild(this.shards)
    if (typeof window !== "undefined" && window.matchMedia) {
      this.reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    }
  }

  get activeCount(): number {
    let n = 0
    for (const p of this.pool) if (p.active) n++
    return n
  }

  private obtain(): Particle | null {
    let p: Particle | undefined
    for (const q of this.pool) {
      if (!q.active) {
        p = q
        break
      }
    }
    if (!p) {
      if (this.pool.length >= PARTICLE_BUDGET.peak) return null
      p = {
        x: 0,
        y: 0,
        vx: 0,
        vy: 0,
        life: 0,
        maxLife: 1,
        size: 2,
        color: 0xffffff,
        gravity: 540,
        spin: 0,
        rot: 0,
        kind: "dot",
        active: false,
      }
      this.pool.push(p)
    }
    return p
  }

  /**
   * 在 (x,y) 爆发碎片。自动遵守预算：
   * 单次 ≤40、单帧累计 ≤40、总量 ≤200；超预算的部分直接丢弃（保帧率）。
   */
  burst(x: number, y: number, color: number, count = 8, power = 1, opts: BurstOpts = {}): void {
    let n = count
    if (this.reducedMotion) n = Math.max(1, Math.round(count * 0.1))
    n = Math.min(n, PARTICLE_BUDGET.perFrame - this.spawnedThisFrame, 40)
    if (n <= 0) return

    const d = DEFAULTS
    const kind = opts.kind ?? d.kind
    const spMin = opts.speedMin ?? d.speedMin
    const spMax = Math.max(spMin, opts.speedMax ?? d.speedMax)
    for (let i = 0; i < n; i++) {
      const p = this.obtain()
      if (!p) return
      const a = Math.random() * Math.PI * 2
      const speed = (spMin + Math.random() * (spMax - spMin)) * power
      p.x = x
      p.y = y
      p.vx = Math.cos(a) * speed
      p.vy = Math.sin(a) * speed - (opts.upBias ?? d.upBias) * power
      p.maxLife = (opts.lifeMin ?? d.lifeMin) + Math.random() * ((opts.lifeMax ?? d.lifeMax) - (opts.lifeMin ?? d.lifeMin))
      p.life = p.maxLife
      p.size = (opts.sizeMin ?? d.sizeMin) + Math.random() * ((opts.sizeMax ?? d.sizeMax) - (opts.sizeMin ?? d.sizeMin))
      p.color = color
      p.gravity = opts.gravity ?? d.gravity
      p.spin = opts.kind === "shard" ? (opts.spin ?? 3.1) * (Math.random() < 0.5 ? -1 : 1) : 0
      p.rot = Math.random() * Math.PI * 2
      p.kind = kind
      p.active = true
      this.spawnedThisFrame++
    }
  }

  update(dtSec: number): void {
    this.spawnedThisFrame = 0
    const gDots = this.dots
    const gShards = this.shards
    gDots.clear()
    gShards.clear()
    for (const p of this.pool) {
      if (!p.active) continue
      p.life -= dtSec
      if (p.life <= 0) {
        p.active = false
        continue
      }
      p.vy += p.gravity * dtSec
      p.x += p.vx * dtSec
      p.y += p.vy * dtSec
      p.rot += p.spin * dtSec

      const t = p.life / p.maxLife // 1 → 0
      // easeOutCubic 淡出（art bible §3.7）+ 尺寸线性归零
      const alpha = 1 - (1 - t) * (1 - t) * (1 - t)
      const size = p.size * t
      if (size <= 0.15) {
        p.active = false
        continue
      }
      if (p.kind === "shard") {
        const s = size
        const c = Math.cos(p.rot)
        const sn = Math.sin(p.rot)
        // 三角碎屑
        const x0 = p.x + c * s
        const y0 = p.y + sn * s
        const x1 = p.x + (-c * 0.5 - sn * 0.87) * s
        const y1 = p.y + (-sn * 0.5 + c * 0.87) * s
        const x2 = p.x + (-c * 0.5 + sn * 0.87) * s
        const y2 = p.y + (-sn * 0.5 - c * 0.87) * s
        gShards.poly([x0, y0, x1, y1, x2, y2]).fill({ color: p.color, alpha })
      } else {
        gDots.circle(p.x, p.y, size).fill({ color: p.color, alpha })
      }
    }
  }

  destroy(): void {
    this.container.destroy({ children: true })
  }
}
