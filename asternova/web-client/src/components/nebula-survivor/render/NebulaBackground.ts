import { Container, Graphics } from "pixi.js"

import { mulberry32, lerpColor, NB_BG, NEBULA } from "./palette"

/** 逻辑绘制基准面（背景内容按此坐标绘制，再整体 scale 铺满视口） */
const BASE_W = 1280
const BASE_H = 720

type Twinkle = { g: Graphics; base: number; phase: number; speed: number }
type DriftBlob = { x: number; y: number; vx: number; vy: number; sprite: Container }

/**
 * 深空星云背景（终末地式：大块冷色星云缓慢漂移 + 远近两层星点，克制、无扫描线）
 * L0 垂直渐变 · L1 星云团块（漂移）· L2 远星点（静态 + 少量闪烁）。
 * 不用全屏 bloom；柔光靠同心圆堆叠（无 filter，移动端友好）。
 */
export class NebulaBackground {
  /** 缩放层：铺满动态视口（content 内部按 BASE_W×BASE_H 绘制） */
  readonly container = new Container()
  private content = new Container()

  private twinkles: Twinkle[] = []
  private nebulas: DriftBlob[] = []
  private elapsed = 0

  constructor() {
    this.container.addChild(this.content)
    this.build()
  }

  /** 整体等比/拉伸铺满实际视口（星点拉伸不可感知，避免每帧重建） */
  setSize(w: number, h: number): void {
    this.content.scale.set(Math.max(0.01, w / BASE_W), Math.max(0.01, h / BASE_H))
  }

  private build() {
    this.buildL0()
    this.buildL1()
    this.buildL2()
  }

  /** L0 三段垂直渐变（strip 近似，单次绘制） */
  private buildL0() {
    const g = new Graphics()
    const stops = [
      { p: 0, c: NB_BG.top },
      { p: 0.52, c: NB_BG.mid },
      { p: 1, c: NB_BG.bot },
    ]
    const colorAt = (p: number) => {
      for (let i = 0; i < stops.length - 1; i++) {
        const a = stops[i]
        const b = stops[i + 1]
        if (p >= a.p && p <= b.p) return lerpColor(a.c, b.c, (p - a.p) / (b.p - a.p))
      }
      return stops[stops.length - 1].c
    }
    const strips = 72
    const sh = BASE_H / strips
    for (let i = 0; i < strips; i++) {
      const p = strips === 1 ? 0 : i / (strips - 1)
      g.rect(0, i * sh, BASE_W, sh + 1).fill({ color: colorAt(p), alpha: 1 })
    }
    this.content.addChild(g)
  }

  /** L1 星云团块：3 个大柔光径向斑（冷青/紫/品红，低饱和），缓慢漂移 */
  private buildL1() {
    const rnd = mulberry32(20260830)
    const blobs = [
      { x: BASE_W * 0.2, y: BASE_H * 0.24, r: 340, color: NEBULA.azurite, a: 0.12 },
      { x: BASE_W * 0.82, y: BASE_H * 0.32, r: 300, color: 0x8a6cff, a: 0.11 },
      { x: BASE_W * 0.52, y: BASE_H * 0.82, r: 380, color: 0x5a4acf, a: 0.1 },
    ]
    for (const b of blobs) {
      const c = new Container()
      const layers = 8
      for (let i = layers; i >= 1; i--) {
        const rr = (b.r * i) / layers
        const aa = (b.a * (layers - i + 1)) / ((layers * (layers + 1)) / 2)
        const lg = new Graphics()
        lg.circle(0, 0, rr).fill({ color: b.color, alpha: aa })
        c.addChild(lg)
      }
      c.position.set(b.x, b.y)
      this.content.addChild(c)
      this.nebulas.push({
        x: b.x,
        y: b.y,
        vx: (rnd() - 0.5) * 5,
        vy: (rnd() - 0.5) * 5,
        sprite: c,
      })
    }
  }

  /** L2 远星点：静态密集 + 少量闪烁（两层，制造视差纵深） */
  private buildL2() {
    const rnd = mulberry32(777)
    const g = new Graphics()
    const count = Math.floor((BASE_W * BASE_H) / 2600)
    for (let i = 0; i < count; i++) {
      const x = rnd() * BASE_W
      const y = rnd() * BASE_H
      const r = 0.4 + rnd() * 1.0
      const a = 0.18 + rnd() * 0.55
      const warm = rnd() < 0.12
      g.circle(x, y, r).fill({ color: warm ? 0xffd9a8 : 0xffffff, alpha: a })
    }
    this.content.addChild(g)

    const twinkleCount = 16
    for (let i = 0; i < twinkleCount; i++) {
      const tg = new Graphics()
      const base = 0.45 + rnd() * 0.5
      tg.circle(0, 0, 0.9 + rnd() * 0.9).fill({ color: 0xffffff, alpha: base })
      tg.position.set(rnd() * BASE_W, rnd() * BASE_H)
      this.content.addChild(tg)
      this.twinkles.push({ g: tg, base, phase: rnd() * Math.PI * 2, speed: 0.8 + rnd() * 1.8 })
    }
  }

  /** 每帧驱动：星云漂移 + 星点闪烁。dtSec 为秒。 */
  update(dtSec: number) {
    this.elapsed += dtSec

    for (const n of this.nebulas) {
      n.x += n.vx * dtSec
      n.y += n.vy * dtSec
      if (n.x < -140 || n.x > BASE_W + 140) n.vx *= -1
      if (n.y < -140 || n.y > BASE_H + 140) n.vy *= -1
      n.sprite.position.set(n.x, n.y)
    }

    for (const tw of this.twinkles) {
      const a = tw.base * (0.55 + 0.45 * Math.sin(this.elapsed * tw.speed + tw.phase))
      tw.g.alpha = Math.max(0, a)
    }
  }

  destroy(): void {
    this.container.destroy({ children: true })
  }
}
