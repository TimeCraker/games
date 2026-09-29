import { Container, Graphics, Sprite, TilingSprite } from "pixi.js"

import { BG_GRADIENT, HEIGHT, PALETTE, WIDTH } from "../constants"
import { ART, dotTexture, grainTexture, nebulaBandTexture, vignetteTexture } from "./artAssets"

/** mulberry32 确定性 PRNG —— 星点/结构布局稳定（不依赖 Math.random） */
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

/**
 * 旋转椭圆描边（Pixi v8 Graphics.ellipse 不支持 rotation 参数）——
 * 48 段折线近似，仅用于静态背景结构，一次性绘制后不再重绘。
 */
function strokeRotatedEllipse(
  g: Graphics,
  cx: number,
  cy: number,
  rx: number,
  ry: number,
  rot: number,
  width: number,
  color: number,
  alpha: number,
): void {
  const N = 48
  const cosR = Math.cos(rot)
  const sinR = Math.sin(rot)
  for (let i = 0; i <= N; i++) {
    const a = (i / N) * Math.PI * 2
    const x = Math.cos(a) * rx
    const y = Math.sin(a) * ry
    const px = cx + x * cosR - y * sinR
    const py = cy + x * sinR + y * cosR
    if (i === 0) g.moveTo(px, py)
    else g.lineTo(px, py)
  }
  g.stroke({ width, color, alpha })
}

interface Star {
  g: Sprite
  x: number
  y: number
  vx: number
  vy: number
  base: number
  breath: number
}

interface DriftBand {
  g: Sprite
  x: number
  vx: number
  halfW: number
}

/**
 * 深空背景（art bible §3.6 升级版，2026-09-28 制作人判决翻案）：
 * 旧版「黑纸撒星」废黜 —— 本轮补足真正的深空纵深：
 * L0 三段渐变 · L0.5 光污染（顶暖下亮，下半截不死黑）· L1 巨型结构剪影
 * （观星台环形轨道 + 巨型星象仪轮廓 + 行星弧线，占背景 30%+）· L2 形状明确的
 * 多层视差星云带 · L3 星尘上疏下密双层视差 · L4 暗角颗粒。
 * 全部静态 Graphics / 合批 Sprite：零每帧整层重绘、零 blur filter。
 */
export class StarFieldBg {
  readonly container = new Container()

  private stars: Star[] = []
  private bands: DriftBand[] = []
  private elapsed = 0
  private reducedMotion = false

  constructor() {
    this.reducedMotion =
      typeof window !== "undefined" && !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    this.buildL0()
    this.buildLightPollution()
    this.buildStructures()
    this.buildNebulaBands()
    this.buildStars()
    this.buildSideWalls()
    this.buildL4()
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

  /**
   * 光污染渐变（判决 1：「画面下半截不能是大片死黑」）：
   * 顶部 = 发射器方向的暖琥珀溢光；底部 = 冷灰蓝的地照提亮（silhouette 反衬）。
   * 用 48 strip 单次绘制，色相只在 amber/ink 派生明度内。
   */
  private buildLightPollution(): void {
    const g = new Graphics()
    const strips = 48
    const sh = HEIGHT / strips
    for (let i = 0; i < strips; i++) {
      const p = i / (strips - 1)
      // 顶暖：0→0.42 段从 amber@9% 衰减到 0
      if (p < 0.42) {
        const k = 1 - p / 0.42
        g.rect(0, i * sh, WIDTH, sh + 1).fill({ color: PALETTE.amber, alpha: 0.05 * k * k })
      }
      // 下亮：0.55→1 段冷灰蓝提亮（0x1a222c 派生自 ink-500/600 明度），末端反而更亮
      if (p > 0.5) {
        const k = (p - 0.5) / 0.5
        const col = lerpColor(0x0b0d12, 0x232c36, Math.min(1, k * 1.15))
        g.rect(0, i * sh, WIDTH, sh + 1).fill({ color: col, alpha: 0.5 * k + 0.14 })
      }
    }
    this.container.addChild(g)
  }

  /**
   * 巨型结构剪影（判决 1：占背景 30%+ 面积；本轮补差 2：描边亮度 +50% 一眼可辨）——
   * ① 行星弧线（左下巨型天体边缘 + 暗环）② 巨型星象仪同心环轨（上部主场）
   * ③ 观星台环形轨道（斜切全场的轨道弧）④ 环上刻度钉点。
   * 全部一次绘制的 Graphics；描边冷灰 @17–39%（上轮 0.14–0.26 ×1.5），行星 rim 走 amber 低 alpha（禁霓虹）。
   */
  private buildStructures(): void {
    const g = new Graphics()
    const rnd = mulberry32(20260928)

    // ---- ① 行星弧线：圆心 (200, 1620) r=560，仅上缘露出（左下 ~22% 面积） ----
    const pcx = 200
    const pcy = 1620
    const pr = 560
    // 行星体：比背景略亮的冷灰面（剪影感），上缘渐亮
    g.circle(pcx, pcy, pr).fill({ color: 0x1a222c, alpha: 0.95 })
    // 弧缘内描边（amber 极淡 = 反射恒星光）
    g.arc(pcx, pcy, pr - 1, Math.PI * 1.12, Math.PI * 1.92).stroke({ width: 3, color: PALETTE.amber, alpha: 0.33 })
    g.arc(pcx, pcy, pr - 8, Math.PI * 1.18, Math.PI * 1.86).stroke({ width: 1.5, color: PALETTE.amberBright, alpha: 0.2 })
    // 暗环（行星环剪影）：两条扁椭圆
    for (const [rx, ry, a] of [
      [720, 92, 0.17],
      [780, 104, 0.11],
    ] as const) {
      strokeRotatedEllipse(g, pcx - 30, pcy - 80, rx, ry, -0.18, 3, ART.fog400, a)
    }
    // 行星表面经纬微线（极淡，只在上缘可见区）
    for (let i = 0; i < 5; i++) {
      const rr = pr * (0.55 + i * 0.09)
      g.arc(pcx, pcy, rr, Math.PI * 1.22, Math.PI * 1.82).stroke({ width: 1, color: ART.ink500, alpha: 0.33 })
    }

    // ---- ② 巨型星象仪轮廓：同心环 + 子午弧，圆心 (360, 420) ----
    const acx = 360
    const acy = 420
    for (const [r, a] of [
      [300, 0.33],
      [368, 0.27],
      [448, 0.21],
    ] as const) {
      g.circle(acx, acy, r).stroke({ width: 1.6, color: ART.fog400, alpha: a })
    }
    // 外环刻度钉（赤道仪语言）：48 根，每 6° 一根，主刻度加长
    for (let deg = 0; deg < 360; deg += 7.5) {
      const a = (deg * Math.PI) / 180
      const major = deg % 30 === 0
      const r0 = 448
      const r1 = r0 + (major ? 14 : 7)
      g.moveTo(acx + Math.cos(a) * r0, acy + Math.sin(a) * r0)
        .lineTo(acx + Math.cos(a) * r1, acy + Math.sin(a) * r1)
        .stroke({ width: 1, color: ART.fog400, alpha: major ? 0.39 : 0.23 })
    }
    // 子午弧 ×3（旋转椭圆，形成球体框架感）
    for (const rot of [-0.5, 0.15, 0.8]) {
      strokeRotatedEllipse(g, acx, acy, 448, 190, rot, 1.2, ART.fog400, 0.23)
    }
    // 极轴短线
    g.moveTo(acx, acy - 470).lineTo(acx, acy + 470).stroke({ width: 1, color: ART.fog400, alpha: 0.18 })

    // ---- ③ 观星台环形轨道：大椭圆弧斜切中下部 ----
    strokeRotatedEllipse(g, 360, 980, 640, 120, -0.12, 2.5, ART.fog400, 0.3)
    strokeRotatedEllipse(g, 360, 980, 600, 104, -0.12, 1.2, ART.fog400, 0.2)
    // 轨道上的站点方块（剪影细节）
    for (let i = 0; i < 9; i++) {
      const a = -0.12 + (i / 8) * Math.PI * 1.05 + 0.12
      const x = 360 + Math.cos(a) * 620
      const y = 980 + Math.sin(a) * 112
      g.rect(x - 8, y - 3.5, 16, 7).fill({ color: ART.ink500, alpha: 0.85 })
      g.rect(x - 8, y - 3.5, 16, 7).stroke({ width: 1, color: ART.fog400, alpha: 0.3 })
    }

    // ---- ④ 观测舱剪影组（轨道旁的小型结构，随机但确定性） ----
    for (let i = 0; i < 6; i++) {
      const x = 80 + rnd() * 560
      const y = 880 + rnd() * 160
      const w = 26 + rnd() * 40
      const h = 12 + rnd() * 22
      g.rect(x, y, w, h).fill({ color: 0x161c26, alpha: 0.9 })
      g.rect(x, y, w, 2).stroke({ width: 1, color: ART.fog400, alpha: 0.34 })
    }

    this.container.addChild(g)
  }

  /**
   * 两侧仪器墙（本轮补差 4：侧边区域加层次细节，贴「深空观星台」母题）——
   * 双立柱面板 + 柱间管线与接头环 + 板缝铆钉 + 内缘刻度柱 + 仪器壁龛（左右非对称）。
   * 全部一次绘制的 Graphics（零每帧成本）；alpha 压在 0.12–0.55，
   * 是「墙的结构」不是发光装饰，整体亮度低于钉板主体、不抢戏。
   */
  private buildSideWalls(): void {
    const g = new Graphics()
    const seamStep = 150
    for (const side of [0, 1] as const) {
      // lx = 距外缘距离（0..72）；X 映射到世界 x（右墙镜像）
      const X = (lx: number) => (side === 0 ? lx : WIDTH - lx)
      const seamOff = side === 0 ? 30 : 105 // 左右错缝，避免镜像印章感
      const nicheYs = side === 0 ? [340, 820, 1160] : [220, 640, 1040]

      // ① 外立柱面板 + 内立柱面板（双柱，冷灰面 + 亮缘）
      for (const [lx0, lx1, fillA] of [
        [6, 30, 0.55],
        [38, 58, 0.4],
      ] as const) {
        const xa = X(lx0)
        const xb = X(lx1)
        g.rect(Math.min(xa, xb), 0, Math.abs(xb - xa), HEIGHT).fill({ color: ART.ink700, alpha: fillA })
        g.moveTo(xa, 0).lineTo(xa, HEIGHT).stroke({ width: 1, color: ART.fog400, alpha: 0.22 })
        g.moveTo(xb, 0).lineTo(xb, HEIGHT).stroke({ width: 1, color: ART.fog400, alpha: 0.18 })
      }

      // ② 柱间暗槽 + 竖直管线（双线 + 接头环）
      const xc = X(34)
      g.rect(Math.min(X(30), X(38)), 0, 8, HEIGHT).fill({ color: ART.ink600, alpha: 0.5 })
      g.moveTo(xc, 0).lineTo(xc, HEIGHT).stroke({ width: 2, color: ART.ink500, alpha: 0.7 })
      const xh = xc + (side === 0 ? -1.5 : 1.5)
      g.moveTo(xh, 0).lineTo(xh, HEIGHT).stroke({ width: 1, color: ART.fog400, alpha: 0.12 })
      for (let y = seamOff; y < HEIGHT; y += 220) {
        g.rect(Math.min(X(31), X(37)) , y - 3, 6, 6).fill({ color: ART.brass, alpha: 0.35 })
      }

      // ③ 横向板缝 + 铆钉
      for (let y = seamOff; y < HEIGHT; y += seamStep) {
        g.moveTo(X(6), y).lineTo(X(58), y).stroke({ width: 1, color: ART.fog400, alpha: 0.2 })
        for (const lx of [14, 22, 48]) {
          g.circle(X(lx), y, 2.2).fill({ color: ART.fog400, alpha: 0.3 })
          g.circle(X(lx), y, 2.2).stroke({ width: 1, color: ART.ink600, alpha: 0.5 })
        }
      }

      // ④ 内缘刻度柱（赤道仪语言：每 26px 小齿、每 4 齿主齿）
      for (let i = 0, y = 20; y < HEIGHT; i++, y += 26) {
        const major = i % 4 === 0
        const len = major ? 9 : 4
        g.moveTo(X(62), y).lineTo(X(62 + len), y).stroke({
          width: 1,
          color: ART.fog400,
          alpha: major ? 0.38 : 0.25,
        })
      }

      // ⑤ 仪器壁龛：圆角面板 + 琥珀指示点 + 细读数线（非对称布局）
      for (const ny of nicheYs) {
        const xa = Math.min(X(38), X(60))
        g.roundRect(xa, ny - 20, 22, 40, 4).fill({ color: ART.ink600, alpha: 0.55 })
        g.roundRect(xa, ny - 20, 22, 40, 4).stroke({ width: 1, color: ART.brass, alpha: 0.4 })
        g.circle(xa + 11, ny - 8, 1.8).fill({ color: PALETTE.amberBright, alpha: 0.5 })
        g.moveTo(xa + 5, ny + 6).lineTo(xa + 17, ny + 6).stroke({ width: 1, color: ART.fog400, alpha: 0.3 })
        g.moveTo(xa + 5, ny + 11).lineTo(xa + 12, ny + 11).stroke({ width: 1, color: ART.fog400, alpha: 0.22 })
      }

      // ⑥ 斜撑（每 500px 一根，结构感）
      for (let y = seamOff + 250; y < HEIGHT; y += 500) {
        g.moveTo(X(6), y).lineTo(X(30), y + 60).stroke({ width: 1, color: ART.fog400, alpha: 0.12 })
      }
    }
    this.container.addChild(g)
  }

  /**
   * 星云带 ×3（判决 1：「形状明确的云带，不是两团模糊」）——
   * 预烘焙 nebulaBandTexture，三层不同深度/速度水平漂移（视差）。
   * reduced-motion 时停漂。
   */
  private buildNebulaBands(): void {
    const mk = (w: number, h: number, seed: number, x: number, y: number, alpha: number, vx: number, rot = 0) => {
      const g = new Sprite({ texture: nebulaBandTexture(w, h, seed) })
      g.anchor.set(0.5)
      g.position.set(x, y)
      g.alpha = alpha
      g.rotation = rot
      this.container.addChild(g)
      this.bands.push({ g, x, vx, halfW: w / 2 })
    }
    // 远层：大而淡，慢速；中层；近层：更亮更快（视差 0.6 / 1.4 / 2.6 px/s）
    mk(1240, 300, 11, WIDTH * 0.42, HEIGHT * 0.30, 0.85, 0.6, -0.05)
    mk(1100, 260, 23, WIDTH * 0.58, HEIGHT * 0.62, 0.78, 1.4, 0.04)
    mk(980, 220, 37, WIDTH * 0.36, HEIGHT * 0.86, 0.72, 2.6, -0.03)
  }

  /** 星尘：上疏下密（y^0.72 偏置）+ 双层视差；全屏 ≤3 颗呼吸。 */
  private buildStars(): void {
    const rnd = mulberry32(20260928)
    const near = 34
    const far = 78
    const tex = dotTexture()
    const mk = (count: number, speed: number, rBase: number) => {
      for (let i = 0; i < count; i++) {
        const g = new Sprite({ texture: tex })
        const amber = rnd() < 0.18
        const r = rBase * (0.7 + rnd() * 0.6)
        const a = 0.2 + rnd() * 0.25
        g.anchor.set(0.5)
        g.tint = amber ? PALETTE.amberPale : ART.fog400
        g.alpha = a
        const d = r * 2.4
        g.width = d
        g.height = d
        const x = rnd() * WIDTH
        // 上疏下密：pow<1 把均匀分布压向底部
        const y = HEIGHT * Math.pow(rnd(), 0.72)
        g.position.set(x, y)
        this.container.addChild(g)
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

    for (let i = 0; i < 3 && i < this.stars.length; i++) {
      this.stars[i * 7 % this.stars.length].breath = (i / 3) * Math.PI * 2
    }
  }

  /** L4 暗角（下缘减淡防死黑）+ 颗粒（140px tile，opacity 0.03）。 */
  private buildL4(): void {
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

  /** 每帧驱动：星尘漂移 + 星云带视差漂移 + 呼吸。reduced-motion 全停。 */
  update(dtSec: number): void {
    this.elapsed += dtSec
    if (this.reducedMotion) return

    for (const s of this.stars) {
      s.x += s.vx * dtSec
      s.y += s.vy * dtSec
      if (s.x < -4) s.x += WIDTH + 8
      else if (s.x > WIDTH + 4) s.x -= WIDTH + 8
      if (s.y < -4) s.y += HEIGHT + 8
      else if (s.y > HEIGHT + 4) s.y -= HEIGHT + 8
      s.g.position.set(s.x, s.y)
      if (s.breath >= 0) {
        const k = 0.5 + 0.5 * Math.sin((this.elapsed / 2.4) * Math.PI * 2 + s.breath)
        s.g.alpha = 0.55 + 0.45 * k
      }
    }

    // 星云带：极慢水平漂移 + 环绕（视差层）
    for (const b of this.bands) {
      b.x += b.vx * dtSec
      const span = WIDTH + b.halfW * 2
      if (b.x > WIDTH + b.halfW) b.x -= span
      else if (b.x < -b.halfW) b.x += span
      b.g.position.set(b.x, b.g.position.y)
    }
  }
}
