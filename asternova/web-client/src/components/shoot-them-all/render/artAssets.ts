import { Texture } from "pixi.js"

/**
 * 画布层预烘焙贴图工厂（art bible §8 资产 1/3/4/5/6/8/9/18）。
 *
 * 全部离屏 canvas 2D 一次性生成、反复复用 —— 发光一律预烘焙径向渐变，
 * 禁逐帧 blur filter（art bible §7 60fps 硬约束）。
 *
 * 色值来源：constants.PALETTE / BG_GRADIENT + art bible §2.2 允许的派生色
 * （brass / dangerHi / sparkWhite）与 §2.5 写死的中性灰面值（ink/fog）。
 * 派生色不进 constants.ts（引擎契约冻结），集中在本文件并标注出处。
 */

// ---- art bible §2.2 允许的派生色（同色相只动明度，禁止再扩） ----
export const ART = {
  /** 重弹黄铜体、发射器暗面（= CSS --amber-600） */
  brass: 0xa87c24,
  /** 炸弹钉高光点（预留） */
  dangerHi: 0xe07a62,
  /** 火花 / 折射线（一律带 alpha 使用） */
  sparkWhite: 0xffffff,
  // §2.5 中性灰（冷灰，无色相漂移）：石头双面 / 刻度 / 星尘
  ink500: 0x2e3339,
  ink600: 0x22262b,
  ink700: 0x181b1f,
  fog100: 0xe2e5e8,
  fog400: 0x6b7480,
} as const

interface CacheEntry {
  tex: Texture
}

const cache = new Map<string, CacheEntry>()

function makeCanvas(w: number, h: number): HTMLCanvasElement {
  const c = document.createElement("canvas")
  c.width = w
  c.height = h
  return c
}

/** 取缓存贴图；被 app.destroy({texture:true}) 回收后自动重建（StrictMode 双挂载安全）。 */
function cached(key: string, build: () => Texture): Texture {
  const hit = cache.get(key)
  if (hit && !(hit.tex as { destroyed?: boolean }).destroyed) return hit.tex
  const tex = build()
  cache.set(key, { tex })
  return tex
}

// ---- 发光（art bible §8-6：预烘焙径向渐变 sprite，禁 blur filter） ----

/** 白色径向柔光（用 sprite.tint 着色，alpha 控强度）。 */
export function glowTexture(radius: number, key: string): Texture {
  return cached(`glow:${key}:${radius}`, () => {
    const size = radius * 2
    const c = makeCanvas(size, size)
    const ctx = c.getContext("2d")!
    const g = ctx.createRadialGradient(radius, radius, 0, radius, radius, radius)
    g.addColorStop(0, "rgba(255,255,255,1)")
    g.addColorStop(0.35, "rgba(255,255,255,0.42)")
    g.addColorStop(0.7, "rgba(255,255,255,0.12)")
    g.addColorStop(1, "rgba(255,255,255,0)")
    ctx.fillStyle = g
    ctx.fillRect(0, 0, size, size)
    return Texture.from(c)
  })
}

// ---- 星云霾（art bible §8-3：ink-700 @8% 径向，固定不滚动） ----

export function nebulaTexture(radius: number): Texture {
  return cached(`nebula:${radius}`, () => {
    const size = radius * 2
    const c = makeCanvas(size, size)
    const ctx = c.getContext("2d")!
    const g = ctx.createRadialGradient(radius, radius, 0, radius, radius, radius)
    // --ink-700 #181B1F @8% → 0
    g.addColorStop(0, "rgba(24,27,31,0.08)")
    g.addColorStop(0.55, "rgba(24,27,31,0.035)")
    g.addColorStop(1, "rgba(24,27,31,0)")
    ctx.fillStyle = g
    ctx.fillRect(0, 0, size, size)
    return Texture.from(c)
  })
}

// ---- 暗角（art bible §8-4：中心到四角变暗 35%） ----

export function vignetteTexture(w: number, h: number): Texture {
  return cached(`vignette:${w}x${h}`, () => {
    const c = makeCanvas(w, h)
    const ctx = c.getContext("2d")!
    const r = Math.hypot(w, h) / 2
    const g = ctx.createRadialGradient(w / 2, h / 2, r * 0.42, w / 2, h / 2, r)
    g.addColorStop(0, "rgba(0,0,0,0)")
    g.addColorStop(0.65, "rgba(0,0,0,0.16)")
    g.addColorStop(1, "rgba(0,0,0,0.35)")
    ctx.fillStyle = g
    ctx.fillRect(0, 0, w, h)
    return Texture.from(c)
  })
}

// ---- 颗粒噪点 tile（art bible §8-4：feTurbulence 同款，140px tile，opacity 0.03） ----

export function grainTexture(): Texture {
  return cached("grain140", () => {
    const s = 140
    const c = makeCanvas(s, s)
    const ctx = c.getContext("2d")!
    const img = ctx.createImageData(s, s)
    // 确定性伪随机（mulberry32），避免每次刷新颗粒闪变
    let a = 20260928
    const rnd = () => {
      a |= 0
      a = (a + 0x6d2b79f5) | 0
      let t = Math.imul(a ^ (a >>> 15), 1 | a)
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296
    }
    for (let i = 0; i < s * s; i++) {
      const v = 120 + rnd() * 135
      img.data[i * 4] = v
      img.data[i * 4 + 1] = v
      img.data[i * 4 + 2] = v
      img.data[i * 4 + 3] = 255
    }
    ctx.putImageData(img, 0, 0)
    return Texture.from(c)
  })
}

// ---- 球体（art bible §8-5：圆 + 描边 + 高光点 + 纹理弧线，64px 缓存） ----
// 绘制基准：64×64 贴图内按 2× 逻辑尺寸绘制（球 r=9 → 18px），使用时 scale 0.5。

function ballBase(
  draw: (ctx: CanvasRenderingContext2D, r: number) => void,
  key: string,
  radiusInTex: number,
): Texture {
  return cached(`ball:${key}`, () => {
    const c = makeCanvas(64, 64)
    const ctx = c.getContext("2d")!
    ctx.translate(32, 32)
    draw(ctx, radiusInTex)
    return Texture.from(c)
  })
}

export function ballTexture(kind: "standard" | "blast" | "pierce" | "heavy"): Texture {
  switch (kind) {
    case "standard":
      return ballBase(
        (ctx, r) => {
          // 主体 amber + amberBright 描边
          ctx.beginPath()
          ctx.arc(0, 0, r, 0, Math.PI * 2)
          ctx.fillStyle = "#d8a33c"
          ctx.fill()
          ctx.lineWidth = 3 // 1.5px 逻辑
          ctx.strokeStyle = "#e9be69"
          ctx.stroke()
          // 表面 2 道极浅弧线纹理 brass @25%
          ctx.lineWidth = 2
          ctx.strokeStyle = "rgba(168,124,36,0.25)"
          ctx.beginPath()
          ctx.arc(0, r * 0.15, r * 0.62, Math.PI * 0.15, Math.PI * 0.75)
          ctx.stroke()
          ctx.beginPath()
          ctx.arc(0, r * 0.3, r * 0.45, Math.PI * 0.25, Math.PI * 0.7)
          ctx.stroke()
          // 顶部 40% 弧线 amberPale @40%
          ctx.lineWidth = 2.5
          ctx.strokeStyle = "rgba(242,215,155,0.4)"
          ctx.beginPath()
          ctx.arc(0, 0, r * 0.72, -Math.PI * 0.72, -Math.PI * 0.28)
          ctx.stroke()
          // 左上高光点 r=2.5（偏移 30%）
          ctx.beginPath()
          ctx.arc(-r * 0.3, -r * 0.35, 5, 0, Math.PI * 2)
          ctx.fillStyle = "#f2d79b"
          ctx.fill()
        },
        "standard",
        18,
      )
    case "blast":
      return ballBase(
        (ctx, r) => {
          ctx.beginPath()
          ctx.arc(0, 0, r, 0, Math.PI * 2)
          ctx.fillStyle = "#e9be69"
          ctx.fill()
          ctx.lineWidth = 3
          ctx.strokeStyle = "#d8a33c"
          ctx.stroke()
          // 核外一圈 brass 暗环（待爆火成岩）
          ctx.lineWidth = 3
          ctx.strokeStyle = "rgba(168,124,36,0.5)"
          ctx.beginPath()
          ctx.arc(0, 0, r * 0.78, 0, Math.PI * 2)
          ctx.stroke()
          // amberPale 核心点 r=3
          ctx.beginPath()
          ctx.arc(0, 0, 6, 0, Math.PI * 2)
          ctx.fillStyle = "#f2d79b"
          ctx.fill()
        },
        "blast",
        18,
      )
    case "pierce":
      return ballBase(
        (ctx, r) => {
          // 体态略扁（scaleX 1.12）表现速度感
          ctx.save()
          ctx.scale(1.12, 1)
          ctx.beginPath()
          ctx.arc(0, 0, r, 0, Math.PI * 2)
          ctx.fillStyle = "#f2d79b"
          ctx.fill()
          ctx.lineWidth = 2
          ctx.strokeStyle = "#d8a33c"
          ctx.stroke()
          ctx.restore()
          // sparkWhite 高光点 @70%
          ctx.beginPath()
          ctx.arc(-r * 0.22, -r * 0.3, 5, 0, Math.PI * 2)
          ctx.fillStyle = "rgba(255,255,255,0.7)"
          ctx.fill()
        },
        "pierce",
        18,
      )
    case "heavy":
      return ballBase(
        (ctx, r) => {
          // 黄铜体，直径 +2px（r=10 → 贴图 20）
          ctx.beginPath()
          ctx.arc(0, 0, r, 0, Math.PI * 2)
          ctx.fillStyle = "#a87c24"
          ctx.fill()
          ctx.lineWidth = 4 // amber 2px
          ctx.strokeStyle = "#d8a33c"
          ctx.stroke()
          // 赤道一圈 --ink-500 金属环
          ctx.lineWidth = 2
          ctx.strokeStyle = "#2e3339"
          ctx.beginPath()
          ctx.ellipse(0, 0, r * 0.92, r * 0.34, 0, 0, Math.PI * 2)
          ctx.stroke()
          // 上缘弧 amberPale @60%
          ctx.lineWidth = 3
          ctx.strokeStyle = "rgba(242,215,155,0.6)"
          ctx.beginPath()
          ctx.arc(0, 0, r * 0.7, -Math.PI * 0.72, -Math.PI * 0.28)
          ctx.stroke()
        },
        "heavy",
        20,
      )
  }
}

// ---- 钉（art bible §8-8/9：六边切面宝石 / 共鸣钉 + 星芒，静态烘焙） ----
// 64×64 贴图，外接圆 r=10 → 贴图内 22（含 4px 翠玉柔光），使用时 scale 0.5。

function hexPoints(r: number): Array<[number, number]> {
  const pts: Array<[number, number]> = []
  for (let i = 0; i < 6; i++) {
    const a = -Math.PI / 2 + (i * Math.PI) / 3
    pts.push([Math.cos(a) * r, Math.sin(a) * r])
  }
  return pts
}

function pathHex(ctx: CanvasRenderingContext2D, r: number): void {
  const pts = hexPoints(r)
  ctx.beginPath()
  ctx.moveTo(pts[0][0], pts[0][1])
  for (let i = 1; i < 6; i++) ctx.lineTo(pts[i][0], pts[i][1])
  ctx.closePath()
}

export function pegTexture(resonance: boolean): Texture {
  return cached(`peg:${resonance ? "res" : "cry"}`, () => {
    const c = makeCanvas(64, 64)
    const ctx = c.getContext("2d")!
    ctx.translate(32, 32)
    const R = 22

    // 外扩翠玉/琥珀柔光（4px @18% 语义，烘焙进贴图）
    const glow = ctx.createRadialGradient(0, 0, R * 0.4, 0, 0, R + 8)
    if (resonance) {
      glow.addColorStop(0, "rgba(216,163,60,0.22)")
      glow.addColorStop(1, "rgba(216,163,60,0)")
    } else {
      glow.addColorStop(0, "rgba(127,179,158,0.18)")
      glow.addColorStop(1, "rgba(127,179,158,0)")
    }
    ctx.fillStyle = glow
    ctx.fillRect(-R - 8, -R - 8, (R + 8) * 2, (R + 8) * 2)

    // 六边形主体 + 3 菱形切面
    pathHex(ctx, R)
    ctx.fillStyle = resonance ? "#d8a33c" : "#7fb39e"
    ctx.fill()
    const pts = hexPoints(R)
    // 左上切面 100%
    const facet = (i0: number, i1: number, color: string) => {
      ctx.beginPath()
      ctx.moveTo(0, 0)
      ctx.lineTo(pts[i0][0], pts[i0][1])
      // 经外接弧中点收一档，形成菱形切面
      const mid = [
        (pts[i0][0] + pts[i1][0]) / 2 * 0.92,
        (pts[i0][1] + pts[i1][1]) / 2 * 0.92,
      ]
      ctx.lineTo(mid[0], mid[1])
      ctx.lineTo(pts[i1][0], pts[i1][1])
      ctx.closePath()
      ctx.fillStyle = color
      ctx.fill()
    }
    if (resonance) {
      facet(5, 0, "rgba(242,215,155,0.95)") // 左上亮
      facet(1, 2, "rgba(216,163,60,0.85)") // 右下
      facet(3, 4, "rgba(168,124,36,0.75)") // 底部
    } else {
      facet(5, 0, "rgba(207,232,222,1)") // jadeLight 100%
      facet(1, 2, "rgba(127,179,158,0.8)") // jade 80%
      facet(3, 4, "rgba(127,179,158,0.6)") // jade 60%
    }

    // 内核高光
    ctx.beginPath()
    ctx.arc(-R * 0.16, -R * 0.22, R * 0.14, 0, Math.PI * 2)
    ctx.fillStyle = resonance ? "rgba(242,215,155,0.9)" : "rgba(207,232,222,0.9)"
    ctx.fill()

    if (resonance) {
      // 中心 4 芒星（arm 5px 逻辑 → 10px 贴图）
      ctx.fillStyle = "#f2d79b"
      ctx.beginPath()
      const arm = 11
      const w = 3
      ctx.moveTo(0, -arm)
      ctx.lineTo(w, -w)
      ctx.lineTo(arm, 0)
      ctx.lineTo(w, w)
      ctx.lineTo(0, arm)
      ctx.lineTo(-w, w)
      ctx.lineTo(-arm, 0)
      ctx.lineTo(-w, -w)
      ctx.closePath()
      ctx.fill()
    }

    // 冷灰描边（line 1px）
    pathHex(ctx, R)
    ctx.lineWidth = 2
    ctx.strokeStyle = resonance ? "rgba(168,124,36,1)" : "rgba(140,148,158,1)"
    ctx.stroke()
    return Texture.from(c)
  })
}

/** 击钉闪白用的纯白六边（叠在钉上 80ms 淡出，art bible §3.7）。 */
export function pegFlashTexture(): Texture {
  return cached("pegFlash", () => {
    const c = makeCanvas(64, 64)
    const ctx = c.getContext("2d")!
    ctx.translate(32, 32)
    pathHex(ctx, 22)
    ctx.fillStyle = "rgba(207,232,222,1)"
    ctx.fill()
    return Texture.from(c)
  })
}

// ---- 星形（art bible §8-18：结算星级 ×3） ----

export function starTexture(): Texture {
  return cached("star", () => {
    const c = makeCanvas(64, 64)
    const ctx = c.getContext("2d")!
    ctx.translate(32, 32)
    ctx.beginPath()
    for (let i = 0; i < 10; i++) {
      const r = i % 2 === 0 ? 26 : 11
      const a = -Math.PI / 2 + (i * Math.PI) / 5
      const x = Math.cos(a) * r
      const y = Math.sin(a) * r
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    }
    ctx.closePath()
    ctx.fillStyle = "#ffffff"
    ctx.fill()
    return Texture.from(c)
  })
}

/** 碎屑三角（石/冰击碎共用形状，sprite.tint 着色）。 */
export function shardTexture(): Texture {
  return cached("shard", () => {
    const c = makeCanvas(16, 16)
    const ctx = c.getContext("2d")!
    ctx.beginPath()
    ctx.moveTo(8, 1)
    ctx.lineTo(15, 14)
    ctx.lineTo(1, 12)
    ctx.closePath()
    ctx.fillStyle = "#ffffff"
    ctx.fill()
    return Texture.from(c)
  })
}

/** 星尘小圆点（白色柔点，sprite.tint 着色；合批省 draw call）。 */
export function dotTexture(): Texture {
  return cached("dot8", () => {
    const s = 8
    const c = makeCanvas(s, s)
    const ctx = c.getContext("2d")!
    const g = ctx.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2)
    g.addColorStop(0, "rgba(255,255,255,1)")
    g.addColorStop(0.55, "rgba(255,255,255,0.85)")
    g.addColorStop(1, "rgba(255,255,255,0)")
    ctx.fillStyle = g
    ctx.fillRect(0, 0, s, s)
    return Texture.from(c)
  })
}
