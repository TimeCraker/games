import { Container, Graphics, Sprite, TilingSprite } from "pixi.js"

import { BG_GRADIENT, HEIGHT, PALETTE, WIDTH } from "../constants"
import { ART, dotTexture, grainTexture, nebulaTexture, vignetteTexture } from "./artAssets"

/** mulberry32 确定性 PRNG —— 星点布局稳定（不依赖 Math.random） */
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

function lerpColor(c1: number, c2: number, t: number): number {
  const r = Math.round(((c1 >> 16) & 0xff) + (((c2 >> 16) & 0xff) - ((c1 >> 16) & 0xff)) * t)
  const g = Math.round(((c1 >> 8) & 0xff) + (((c2 >> 8) & 0xff) - ((c1 >> 8) & 0xff)) * t)
  const b = Math.round((c1 & 0xff) + ((c2 & 0xff) - (c1 & 0xff)) * t)
  return (r << 16) | (g << 8) | b
}

interface Star {
  /** 共享柔点贴图的 Sprite（合批省 draw call） */
  g: Sprite
  x: number
  y: number
  vx: number
  vy: number
  base: number
  /** -1 = 不呼吸；否则呼吸相位 */
  breath: number
}

/**
 * 深空背景（art bible §3.6 L0–L3 四层）：
 * L0 三段垂直渐变（重心压底）· L1 细星尘双层视差（近 4px/s / 远 1.5px/s，最多 3 颗呼吸）
 * · L2 星云霾 ×2（ink-700 @8%，固定不滚动）· L3 暗角 + 颗粒（opacity 0.03）。
 * 扫描线/网格不上画布（art bible §3.6：画布保持底片般干净）。
 */
export class StarFieldBg {
  readonly container = new Container()

  private stars: Star[] = []
  private elapsed = 0
  private reducedMotion = false

  constructor() {
    this.reducedMotion =
      typeof window !== "undefined" && !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    this.buildL0()
    this.buildL1()
    this.buildL2()
    this.buildL3()
  }

  /** L0 三段垂直渐变（64 strip 近似，单次绘制）。 */
  private buildL0(): void {
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
        if (p >= a.p && p <= b.p) return lerpColor(a.c, b.c, (p - a.p) / (b.p - a.p))
      }
      return stops[stops.length - 1].c
    }
    const strips: number = 64
    const sh = HEIGHT / strips
    for (let i = 0; i < strips; i++) {
      const p = strips === 1 ? 0 : i / (strips - 1)
      g.rect(0, i * sh, WIDTH, sh + 1).fill(colorAt(p))
    }
    this.container.addChild(g)
  }

  /** L1 星尘 60–90 颗：远层 1.5px/s + 近层 4px/s 视差微移；≤3 颗 2.4s 呼吸。
   *  全部 Sprite + 共享柔点贴图（合批 1 draw call），避免逐星 Graphics。 */
  private buildL1(): void {
    const rnd = mulberry32(20260928)
    const near = 26
    const far = 48
    const tex = dotTexture()
    const mk = (count: number, speed: number, rBase: number) => {
      for (let i = 0; i < count; i++) {
        const g = new Sprite({ texture: tex })
        const amber = rnd() < 0.18
        const r = rBase * (0.7 + rnd() * 0.6)
        const a = 0.2 + rnd() * 0.25 // alpha 20–45%
        g.anchor.set(0.5)
        g.tint = amber ? PALETTE.amberPale : ART.fog400
        g.alpha = a
        const d = r * 2.4 // 柔点贴图含光晕，略放大
        g.width = d
        g.height = d
        const x = rnd() * WIDTH
        const y = rnd() * HEIGHT
        g.position.set(x, y)
        this.container.addChild(g)
        // 缓慢漂移方向固定为右下偏转（观星台底片感），速度 ≤4px/s
        const ang = -Math.PI / 2 + (rnd() - 0.5) * 0.5
        this.stars.push({
          g,
          x,
          y,
          vx: Math.cos(ang) * speed,
          vy: Math.sin(ang) * speed * 0.35 + speed * 0.2,
          base: a,
          breath: -1,
        })
      }
    }
    mk(far, 1.5, 0.7)
    mk(near, 4, 1.1)

    // 全屏最多 3 颗允许 2.4s 呼吸明灭
    for (let i = 0; i < 3 && i < this.stars.length; i++) {
      this.stars[i * 7 % this.stars.length].breath = (i / 3) * Math.PI * 2
    }
  }

  /** L2 星云霾 ×2（r 280/420，ink-700 @8%，固定不滚动）。 */
  private buildL2(): void {
    const n1 = new Sprite({ texture: nebulaTexture(280) })
    n1.anchor.set(0.5)
    n1.position.set(WIDTH * 0.3, HEIGHT * 0.3)
    const n2 = new Sprite({ texture: nebulaTexture(420) })
    n2.anchor.set(0.5)
    n2.position.set(WIDTH * 0.72, HEIGHT * 0.72)
    this.container.addChild(n1, n2)
  }

  /** L3 暗角（径向变暗 35%）+ 颗粒（140px tile，opacity 0.03）。 */
  private buildL3(): void {
    const vig = new Sprite({ texture: vignetteTexture(WIDTH, HEIGHT) })
    vig.position.set(0, 0)
    this.container.addChild(vig)

    const grain = new TilingSprite({
      texture: grainTexture(),
      width: WIDTH,
      height: HEIGHT,
    })
    grain.alpha = 0.03
    this.container.addChild(grain)
  }

  /** 每帧驱动：星尘漂移 + 呼吸。dtSec 为秒。 */
  update(dtSec: number): void {
    this.elapsed += dtSec
    if (this.reducedMotion) return // 星尘停漂（art bible §5 末）

    for (const s of this.stars) {
      s.x += s.vx * dtSec
      s.y += s.vy * dtSec
      if (s.x < -4) s.x += WIDTH + 8
      else if (s.x > WIDTH + 4) s.x -= WIDTH + 8
      if (s.y < -4) s.y += HEIGHT + 8
      else if (s.y > HEIGHT + 4) s.y -= HEIGHT + 8
      s.g.position.set(s.x, s.y)
      if (s.breath >= 0) {
        // 2.6s→2.4s 周期呼吸，幅度限定在 20–45% 区间内
        const k = 0.5 + 0.5 * Math.sin((this.elapsed / 2.4) * Math.PI * 2 + s.breath)
        s.g.alpha = 0.55 + 0.45 * k
      }
    }
  }
}
