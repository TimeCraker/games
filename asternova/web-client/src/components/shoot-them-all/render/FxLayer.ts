import { Container, Graphics, Sprite, Text } from "pixi.js"

import { HEIGHT, PALETTE, WIDTH } from "../constants"
import { ART, glowTexture, starTexture } from "./artAssets"

/**
 * 瞬时特效层（art bible §3.7/§3.8/§5）：
 * 冲击环 / 击钉白环 / 炮口焰光 / 分数跳字 / 连击跳字 / 星级爆发 / 闪白 / 屏震 / hit-stop。
 *
 * 预算：环与闪光全部走单 Graphics 每帧批量重绘（零 blur filter）；
 * 跳字用 Text 对象池；屏震只平移不旋转、同刻取最大振幅不叠加。
 */

// ---- 缓动（art bible §5） ----
export function easeOutCubic(t: number): number {
  const u = 1 - Math.min(1, Math.max(0, t))
  return 1 - u * u * u
}

export function easeOut(t: number): number {
  const u = 1 - Math.min(1, Math.max(0, t))
  return 1 - u * (2 - u)
}

/** cubic-bezier(0.32, 0.72, 0, 1) —— --ease-instrument（跳字上浮/淡出）。 */
function easeInstrument(t: number): number {
  // 数值求解 x(u)=t 再取 y(u)（Newton 迭代 4 次足够）
  const x1 = 0.32
  const y1 = 0.72
  const x2 = 0
  const y2 = 1
  let u = t
  for (let i = 0; i < 4; i++) {
    const x = 3 * (1 - u) * (1 - u) * u * x1 + 3 * (1 - u) * u * u * x2 + u * u * u
    const dx = 3 * (1 - u) * (1 - u) * x1 + 6 * (1 - u) * u * (x2 - x1) + 3 * u * u * (1 - x2)
    if (Math.abs(dx) < 1e-6) break
    u -= (x - t) / dx
    u = Math.min(1, Math.max(0, u))
  }
  return 3 * (1 - u) * (1 - u) * u * y1 + 3 * (1 - u) * u * u * y2 + u * u * u
}

interface RingFx {
  alive: boolean
  x: number
  y: number
  r0: number
  r1: number
  width: number
  color: number
  alpha0: number
  life: number
  maxLife: number
  ease: (t: number) => number
  /** 前 80ms 内芯（爆裂弹 danger 芯） */
  core?: { color: number; r: number; alpha: number }
}

interface PopupFx {
  alive: boolean
  text: Text
  x0: number
  y0: number
  rise: number
  life: number
  maxLife: number
  pop: number // 0~1 缩放弹跳进度，<0 关闭
}

interface StarFx {
  alive: boolean
  sprite: Sprite
  ring: Graphics
  lit: boolean
  t: number
}

/** 假光照爆发（判决 4：命中闪光照亮周围）——预烘焙柔光 sprite 放大淡出，零 blur。 */
interface LightFx {
  alive: boolean
  sprite: Sprite
  x: number
  y: number
  r0: number
  r1: number
  life: number
  maxLife: number
  alpha0: number
}

/** hit-stop：短冻结（画布层自主时钟，引擎 tick 由 StaPixiApp 按剩余量跳过）。 */
const HIT_STOP_MS = 50

export class FxLayer {
  /** 世界层特效（冲击环/跳字）——随屏震平移 */
  readonly container = new Container()
  /** 全屏覆盖层（闪白/变暗/星级）——钉在屏幕上，不随屏震 */
  readonly overlay = new Container()

  private ringG = new Graphics()
  private rings: RingFx[] = []
  private popups: PopupFx[] = []
  private stars: StarFx[] = []
  private lights: LightFx[] = []

  private flashG: Graphics // 全屏闪白（白）
  private dimG: Graphics // 收束变暗（冷黑）
  private flashAlpha = 0
  private flashDecay = 0
  private dimAlpha = 0

  private shakeMag = 0
  private shakeTime = 0
  private shakeDur = 0
  private shakeXBias = 1

  private hitStopMs = 0

  readonly reducedMotion: boolean

  constructor() {
    this.container.addChild(this.ringG)
    this.dimG = new Graphics()
    this.dimG.rect(0, 0, WIDTH, HEIGHT).fill({ color: 0x050608, alpha: 1 })
    this.dimG.alpha = 0
    this.overlay.addChild(this.dimG)
    this.flashG = new Graphics()
    this.flashG.rect(0, 0, WIDTH, HEIGHT).fill({ color: 0xffffff, alpha: 1 })
    this.flashG.alpha = 0
    this.overlay.addChild(this.flashG)

    this.reducedMotion =
      typeof window !== "undefined" && !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    for (let i = 0; i < 24; i++) {
      this.rings.push(this.blankRing())
    }
    for (let i = 0; i < 10; i++) {
      this.popups.push(this.blankPopup())
    }
    for (let i = 0; i < 8; i++) {
      const sprite = new Sprite({ texture: glowTexture(48, "light") })
      sprite.anchor.set(0.5)
      sprite.blendMode = "add"
      sprite.alpha = 0
      sprite.visible = false
      this.container.addChild(sprite)
      this.lights.push({ alive: false, sprite, x: 0, y: 0, r0: 20, r1: 60, life: 0, maxLife: 0.28, alpha0: 0.5 })
    }
    this.buildStars()
  }

  // ---- 池 ----

  private blankRing(): RingFx {
    return {
      alive: false,
      x: 0,
      y: 0,
      r0: 10,
      r1: 18,
      width: 1,
      color: 0xffffff,
      alpha0: 1,
      life: 0,
      maxLife: 0.2,
      ease: easeOutCubic,
    }
  }

  private blankPopup(): PopupFx {
    const text = new Text({
      text: "",
      style: {
        fontFamily: "'JetBrains Mono', ui-monospace, monospace",
        fontSize: 28,
        fontWeight: "bold",
        fill: 0xe2e5e8,
        letterSpacing: 1,
      },
    })
    text.anchor.set(0.5)
    text.alpha = 0
    this.container.addChild(text)
    return { alive: false, text, x0: 0, y0: 0, rise: 40, life: 0, maxLife: 0.32, pop: -1 }
  }

  private obtainRing(): RingFx {
    for (const r of this.rings) if (!r.alive) return r
    const r = this.blankRing()
    this.rings.push(r)
    return r
  }

  private obtainPopup(): PopupFx {
    for (const p of this.popups) if (!p.alive) return p
    const p = this.blankPopup()
    this.popups.push(p)
    return p
  }

  // ---- 对外 API ----

  /** 通用扩张环（白环 r 10→18 等）。 */
  ring(x: number, y: number, r0: number, r1: number, opts: Partial<Omit<RingFx, "alive" | "life">> = {}): void {
    const r = this.obtainRing()
    r.alive = true
    r.x = x
    r.y = y
    r.r0 = r0
    r.r1 = r1
    r.width = opts.width ?? 1
    r.color = opts.color ?? 0xffffff
    r.alpha0 = opts.alpha0 ?? 0.9
    r.maxLife = opts.maxLife ?? 0.2
    r.life = r.maxLife
    r.ease = opts.ease ?? easeOutCubic
    r.core = opts.core
  }

  /** 爆裂弹双环冲击波（art bible §3.7：外环 20→90 / 内环 20→50 + danger 芯 80ms）。 */
  blastShock(x: number, y: number): void {
    this.ring(x, y, 20, 90, {
      width: 2,
      color: PALETTE.amberPale,
      alpha0: 0.95,
      maxLife: 0.32,
      core: { color: PALETTE.danger, r: 26, alpha: 0.4 },
    })
    this.ring(x, y, 20, 50, {
      width: 1,
      color: ART.sparkWhite,
      alpha0: 0.8,
      maxLife: 0.2,
    })
  }

  /** 击钉白环（r 10→18，200ms）。 */
  pegHitRing(x: number, y: number): void {
    this.ring(x, y, 10, 18, { width: 1, color: ART.sparkWhite, alpha0: 0.85, maxLife: 0.2 })
  }

  /**
   * 假光照爆发（判决 4：命中瞬间照亮周围）——柔光 sprite 从 r0 扩到 r1 并淡出。
   * reduced-motion 退化为强度减半的亮度轻闪（不放大光晕）。
   */
  lightBurst(
    x: number,
    y: number,
    color: number,
    opts: { r0?: number; r1?: number; alpha0?: number; maxLife?: number } = {},
  ): void {
    let slot: LightFx | undefined
    for (const l of this.lights) if (!l.alive) {
      slot = l
      break
    }
    if (!slot) return
    slot.alive = true
    slot.x = x
    slot.y = y
    slot.r0 = opts.r0 ?? 18
    slot.r1 = opts.r1 ?? 56
    slot.alpha0 = this.reducedMotion ? (opts.alpha0 ?? 0.4) * 0.5 : (opts.alpha0 ?? 0.4)
    slot.maxLife = this.reducedMotion ? 0.12 : (opts.maxLife ?? 0.28)
    slot.life = slot.maxLife
    slot.sprite.tint = color
    slot.sprite.position.set(x, y)
    slot.sprite.visible = true
    slot.sprite.alpha = slot.alpha0
  }

  /** 炮口焰光环（r 8→22，180ms）。 */
  muzzleRing(x: number, y: number): void {
    this.ring(x, y, 8, 22, { width: 1, color: ART.sparkWhite, alpha0: 0.9, maxLife: 0.18 })
  }

  /** 分数跳字「+N」。resonance 用琥珀亮色，普通钉用冷灰（art bible §3.7）。 */
  scorePopup(x: number, y: number, gained: number, resonance: boolean): void {
    const p = this.obtainPopup()
    p.alive = true
    p.text.text = `+${gained}`
    p.text.style.fill = resonance ? PALETTE.amberBright : 0x8c949e
    p.text.style.fontSize = resonance ? 32 : 28
    p.x0 = x
    p.y0 = y - 12
    p.rise = 40
    p.maxLife = 0.32
    p.life = p.maxLife
    p.pop = resonance ? 0 : -1
    p.text.alpha = 1
    p.text.position.set(p.x0, p.y0)
    p.text.scale.set(1)
  }

  /** 连击跳字「×N」（scale 1→1.25→1，150ms）。 */
  comboPopup(value: number): void {
    const p = this.obtainPopup()
    p.alive = true
    p.text.text = `×${value}`
    p.text.style.fill = PALETTE.amberBright
    p.text.style.fontSize = 34
    p.x0 = WIDTH / 2
    p.y0 = HEIGHT * 0.3
    p.rise = 28
    p.maxLife = 0.4
    p.life = p.maxLife
    p.pop = 0
    p.text.alpha = 1
    p.text.position.set(p.x0, p.y0)
    p.text.scale.set(1)
  }

  /** 屏震：同刻只取最大振幅（art bible §3.8）。horizontalBias 放大水平分量。 */
  shake(mag: number, horizontalBias = false): void {
    if (this.reducedMotion) {
      // 退化：80ms 全屏亮度 +4% 轻闪
      this.flash(0.04, 0.08)
      return
    }
    this.shakeMag = Math.max(this.shakeMag, mag)
    this.shakeDur = 0.3
    this.shakeTime = 0.3
    this.shakeXBias = horizontalBias ? 1.6 : 1
  }

  /** 全屏闪白（opacity 峰值 → 0，dur 秒）。 */
  flash(peak: number, dur: number): void {
    this.flashAlpha = Math.max(this.flashAlpha, peak)
    this.flashDecay = peak / Math.max(0.016, dur)
    this.flashG.alpha = this.flashAlpha
  }

  /** 过关/失败收束变暗（持续存在的暗层，0 = 关闭）。 */
  setDim(alpha: number): void {
    this.dimAlpha = Math.min(0.72, Math.max(0, alpha))
    this.dimG.alpha = this.dimAlpha
  }

  /** hit-stop：短冻结（仅重弹/爆裂大命中）。 */
  triggerHitStop(): void {
    this.hitStopMs = Math.max(this.hitStopMs, this.reducedMotion ? 0 : HIT_STOP_MS)
  }

  get hitStopRemainingMs(): number {
    return this.hitStopMs
  }

  /** StaPixiApp 每帧扣减 hit-stop 余量；返回是否仍处于冻结。 */
  consumeHitStop(dtMs: number): boolean {
    if (this.hitStopMs <= 0) return false
    this.hitStopMs = Math.max(0, this.hitStopMs - dtMs)
    return this.hitStopMs > 0
  }

  // ---- 星级爆发（art bible §5 动效 9：三颗星逐颗点亮，间隔 160ms） ----

  private buildStars(): void {
    const tex = starTexture()
    for (let i = 0; i < 3; i++) {
      const sprite = new Sprite({ texture: tex })
      sprite.anchor.set(0.5)
      sprite.tint = PALETTE.amber
      sprite.width = 48
      sprite.height = 48
      sprite.position.set(WIDTH / 2 + (i - 1) * 78, 420)
      sprite.alpha = 0
      sprite.visible = false
      const ring = new Graphics()
      this.overlay.addChild(ring)
      this.overlay.addChild(sprite)
      this.stars.push({ alive: false, sprite, ring, lit: false, t: 0 })
    }
  }

  /** 过关：点亮 count 颗星（其余保持暗轮廓），逐颗 160ms 间隔。 */
  starBurst(count: number): void {
    const lit = Math.max(1, Math.min(3, count))
    for (let i = 0; i < 3; i++) {
      const s = this.stars[i]
      s.lit = i < lit
      if (this.reducedMotion) {
        // 直接显示终态
        s.alive = true
        s.t = 1
        s.sprite.alpha = s.lit ? 1 : 0.18
        s.sprite.visible = true
        s.sprite.scale.set(s.lit ? 1 : 0.72)
        s.sprite.tint = s.lit ? PALETTE.amber : ART.ink500
        s.ring.clear()
        continue
      }
      s.alive = true
      s.t = -i * 0.16 // 负值 = 等待点亮
      s.sprite.visible = true
      s.sprite.alpha = 0
      s.ring.clear()
    }
  }

  clearStars(): void {
    for (const s of this.stars) {
      s.alive = false
      s.sprite.visible = false
      s.ring.clear()
    }
  }

  // ---- 每帧 ----

  update(dtSec: number): void {
    // 屏震衰减：300ms 内从峰值 easeOut 衰减至 0（同刻取最大振幅，见 shake()）
    if (this.shakeMag > 0.05 && this.shakeTime > 0) {
      this.shakeTime = Math.max(0, this.shakeTime - dtSec)
      const k = this.shakeDur > 0 ? this.shakeTime / this.shakeDur : 0
      const amp = this.shakeMag * easeOut(k)
      this.shakeOffsetX = (Math.random() * 2 - 1) * amp * this.shakeXBias
      this.shakeOffsetY = (Math.random() * 2 - 1) * amp
    } else {
      this.shakeMag = 0
      this.shakeOffsetX = 0
      this.shakeOffsetY = 0
    }

    // 闪白（白，峰值衰减）与变暗（冷黑，持续）分层管理
    if (this.flashAlpha > 0.001) {
      this.flashAlpha = Math.max(0, this.flashAlpha - this.flashDecay * dtSec)
    }
    this.flashG.alpha = this.flashAlpha
    this.dimG.alpha = this.dimAlpha

    // 冲击环
    this.ringG.clear()
    for (const r of this.rings) {
      if (!r.alive) continue
      r.life -= dtSec
      if (r.life <= 0) {
        r.alive = false
        continue
      }
      const t = 1 - r.life / r.maxLife
      const e = r.ease(t)
      const rad = r.r0 + (r.r1 - r.r0) * e
      const a = r.alpha0 * (1 - t)
      if (r.core && t < 0.25) {
        // 内芯 danger @40% 仅前 80ms
        this.ringG.circle(r.x, r.y, r.core.r).fill({ color: r.core.color, alpha: r.core.alpha * (1 - t / 0.25) })
      }
      this.ringG.circle(r.x, r.y, rad).stroke({ width: r.width, color: r.color, alpha: a })
    }

    // 假光照爆发：柔光 sprite 放大淡出（判决 4：爆闪照亮周围）
    for (const l of this.lights) {
      if (!l.alive) continue
      l.life -= dtSec
      if (l.life <= 0) {
        l.alive = false
        l.sprite.visible = false
        l.sprite.alpha = 0
        continue
      }
      const t = 1 - l.life / l.maxLife
      const e = easeOutCubic(t)
      const rad = l.r0 + (l.r1 - l.r0) * e
      // glowTexture(48) 半径 48px，scale = rad/48
      l.sprite.scale.set(rad / 48)
      l.sprite.alpha = l.alpha0 * (1 - t) * (1 - t * 0.5)
    }

    // 跳字
    for (const p of this.popups) {
      if (!p.alive) continue
      p.life -= dtSec
      if (p.life <= 0) {
        p.alive = false
        p.text.alpha = 0
        continue
      }
      const t = 1 - p.life / p.maxLife
      const e = easeInstrument(t)
      p.text.position.set(p.x0, p.y0 - p.rise * e)
      p.text.alpha = Math.max(0, 1 - t * t)
      if (p.pop >= 0) {
        // scale 1→1.25→1（150ms 级），借用 t 进度做弹跳
        const s = 1 + 0.25 * Math.sin(Math.PI * Math.min(1, t / 0.45))
        p.text.scale.set(s)
      }
    }

    // 星级
    for (const s of this.stars) {
      if (!s.alive) continue
      if (this.reducedMotion) continue
      if (s.t < 0) {
        s.t += dtSec
        if (s.t < 0) {
          s.ring.clear()
          continue
        }
      }
      s.t += dtSec
      const pop = Math.min(1, s.t / 0.2) // 200ms pop
      // scale 0→1.2→1：前 60% 冲到 1.2，后 40% 回落到 1
      const scale = s.lit
        ? pop < 0.6
          ? easeOut(pop / 0.6) * 1.2
          : 1.2 - 0.2 * easeOut((pop - 0.6) / 0.4)
        : 0.72
      s.sprite.scale.set(s.lit ? scale : 0.72)
      s.sprite.alpha = s.lit ? Math.min(1, pop * 1.5) : 0.18
      s.sprite.tint = s.lit ? PALETTE.amber : ART.ink500
      // 外环爆闪 r 20→60（280ms）
      const rt = Math.min(1, s.t / 0.28)
      s.ring.clear()
      if (s.lit && rt < 1) {
        const rr = 20 + 40 * easeOutCubic(rt)
        s.ring.circle(s.sprite.x, s.sprite.y, rr).stroke({
          width: 2,
          color: PALETTE.amberPale,
          alpha: 0.85 * (1 - rt),
        })
      }
    }
  }

  /** 屏震偏移（BattleScene 应用到世界容器）。 */
  shakeOffsetX = 0
  shakeOffsetY = 0

  destroy(): void {
    this.container.destroy({ children: true })
  }
}
