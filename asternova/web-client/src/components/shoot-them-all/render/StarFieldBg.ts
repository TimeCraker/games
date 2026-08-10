import { Container, Graphics } from "pixi.js"

import { BG_GRADIENT, HEIGHT, PALETTE, WIDTH } from "../constants"

/** mulberry32 确定性 PRNG —— 保证背景星点/星云布局稳定（不依赖 Math.random） */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t
}

function lerpColor(c1: number, c2: number, t: number): number {
  const r = Math.round(lerp((c1 >> 16) & 0xff, (c2 >> 16) & 0xff, t))
  const g = Math.round(lerp((c1 >> 8) & 0xff, (c2 >> 8) & 0xff, t))
  const b = Math.round(lerp(c1 & 0xff, c2 & 0xff, t))
  return (r << 16) | (g << 8) | b
}

type Twinkle = { g: Graphics; base: number; phase: number; speed: number }
type DriftBlob = { x: number; y: number; vx: number; vy: number; sprite: Container }

/**
 * 深空背景（Stage Spec §6.2，4 层叠加，Pixi 绘制）：
 * L0 基底渐变 · L1 星云团块（漂移）· L2 远星点（静态+闪烁）· L3 观测台网格+扫描线。
 * 不用全屏 bloom；柔光靠同心圆堆叠模拟（无 filter，移动端友好）。
 */
export class StarFieldBg {
  readonly container = new Container()

  private twinkles: Twinkle[] = []
  private nebulas: DriftBlob[] = []
  private scan: Graphics
  private elapsed = 0

  constructor() {
    this.buildL0()
    this.buildL1()
    this.buildL2()
    this.scan = this.buildL3()
  }

  /** L0 三段垂直渐变（strip 近似，单次绘制，版本无关） */
  private buildL0() {
    const g = new Graphics()
    const stops = [
      { p: 0, c: BG_GRADIENT.top },
      { p: 0.5, c: BG_GRADIENT.mid },
      { p: 1, c: BG_GRADIENT.bot },
    ]
    const colorAt = (p: number) => {
      for (let i = 0; i < stops.length - 1; i++) {
        const a = stops[i]
        const b = stops[i + 1]
        if (p >= a.p && p <= b.p) {
          return lerpColor(a.c, b.c, (p - a.p) / (b.p - a.p))
        }
      }
      return stops[stops.length - 1].c
    }
    const strips = 64
    const sh = HEIGHT / strips
    for (let i = 0; i < strips; i++) {
      const p = strips === 1 ? 0 : i / (strips - 1)
      g.rect(0, i * sh, WIDTH, sh + 1).fill(colorAt(p))
    }
    this.container.addChild(g)
  }

  /** L1 星云团块：3 个柔光径向斑，缓慢漂移（120s 级周期） */
  private buildL1() {
    const rnd = mulberry32(20260810)
    const blobs = [
      { x: WIDTH * 0.25, y: HEIGHT * 0.22, r: 320, color: PALETTE.azurite, a: 0.1 },
      { x: WIDTH * 0.78, y: HEIGHT * 0.35, r: 280, color: PALETTE.violet, a: 0.09 },
      { x: WIDTH * 0.5, y: HEIGHT * 0.78, r: 360, color: PALETTE.cyan, a: 0.07 },
    ]
    for (const b of blobs) {
      const c = new Container()
      const layers = 7
      for (let i = layers; i >= 1; i--) {
        const rr = (b.r * i) / layers
        const aa = (b.a * (layers - i + 1)) / ((layers * (layers + 1)) / 2)
        const lg = new Graphics()
        lg.circle(0, 0, rr).fill({ color: b.color, alpha: aa })
        c.addChild(lg)
      }
      c.position.set(b.x, b.y)
      this.container.addChild(c)
      this.nebulas.push({
        x: b.x,
        y: b.y,
        vx: (rnd() - 0.5) * 4,
        vy: (rnd() - 0.5) * 4,
        sprite: c,
      })
    }
  }

  /** L2 远星点：静态密集（≈1 颗/2400px²） + 少量闪烁 */
  private buildL2() {
    const rnd = mulberry32(777)
    const g = new Graphics()
    const count = Math.floor((WIDTH * HEIGHT) / 2400)
    for (let i = 0; i < count; i++) {
      const x = rnd() * WIDTH
      const y = rnd() * HEIGHT
      const r = 0.4 + rnd() * 0.9
      const a = 0.25 + rnd() * 0.6
      g.circle(x, y, r).fill({ color: 0xffffff, alpha: a })
    }
    this.container.addChild(g)

    const twinkleCount = 14
    for (let i = 0; i < twinkleCount; i++) {
      const tg = new Graphics()
      const base = 0.4 + rnd() * 0.5
      tg.circle(0, 0, 0.9 + rnd() * 0.8).fill({ color: 0xffffff, alpha: base })
      tg.position.set(rnd() * WIDTH, rnd() * HEIGHT)
      this.container.addChild(tg)
      this.twinkles.push({ g: tg, base, phase: rnd() * Math.PI * 2, speed: 0.8 + rnd() * 1.6 })
    }
  }

  /** L3 观测台网格（极淡）+ 扫描线（8s 周期） */
  private buildL3(): Graphics {
    const grid = new Graphics()
    const step = 64
    for (let x = 0; x <= WIDTH; x += step) {
      grid.moveTo(x, 0).lineTo(x, HEIGHT).stroke({ width: 1, color: 0x9bb0ff, alpha: 0.05 })
    }
    for (let y = 0; y <= HEIGHT; y += step) {
      grid.moveTo(0, y).lineTo(WIDTH, y).stroke({ width: 1, color: 0x9bb0ff, alpha: 0.05 })
    }
    this.container.addChild(grid)

    const scan = new Graphics()
    scan.rect(0, 0, WIDTH, 2).fill({ color: PALETTE.cyan, alpha: 0.5 })
    this.container.addChild(scan)
    return scan
  }

  /** 每帧驱动：星云漂移 + 闪烁 + 扫描线。dtSec 为秒。 */
  update(dtSec: number) {
    this.elapsed += dtSec

    for (const n of this.nebulas) {
      n.x += n.vx * dtSec
      n.y += n.vy * dtSec
      if (n.x < -120 || n.x > WIDTH + 120) n.vx *= -1
      if (n.y < -120 || n.y > HEIGHT + 120) n.vy *= -1
      n.sprite.position.set(n.x, n.y)
    }

    for (const tw of this.twinkles) {
      const a = tw.base * (0.55 + 0.45 * Math.sin(this.elapsed * tw.speed + tw.phase))
      tw.g.alpha = Math.max(0, a)
    }

    const cycle = 8
    const frac = (this.elapsed % cycle) / cycle
    this.scan.position.set(0, frac * (HEIGHT + 40) - 20)
    this.scan.alpha = 0.3 + 0.3 * Math.sin(frac * Math.PI)
  }
}
