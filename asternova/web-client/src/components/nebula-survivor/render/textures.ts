import { Texture } from "pixi.js"

import { mulberry32 } from "../sim/rng"

/**
 * 程序化贴图（canvas 生成 → Texture）。
 * 底板/星云/行星这类「大面积、低细节」的东西用贴图比逐帧矢量便宜得多，
 * 也让分层视差成为可能（白皮书 §10 的底板三层）。
 */
function canvas(size: number): { c: HTMLCanvasElement; x: CanvasRenderingContext2D } {
  const c = document.createElement("canvas")
  c.width = size; c.height = size
  const x = c.getContext("2d")!
  return { c, x }
}

const cache = new Map<string, Texture>()
export function disposeTextures(): void { cache.clear() }

/** 可平铺的星空方块（4 层用不同密度/亮度） */
export function starTile(seed: number, count: number, size: number, alpha: number, bright: number): Texture {
  const key = `star-${seed}-${count}-${size}`
  const hit = cache.get(key); if (hit) return hit
  const { c, x } = canvas(size)
  const rnd = mulberry32(seed)
  // 包边：右上角额外画一份，保证平铺接缝不出现"空带"
  for (let i = 0; i < count; i++) {
    const px = rnd() * size, py = rnd() * size
    const r = (0.4 + rnd() * 0.9) * bright
    const a = alpha * (0.35 + rnd() * 0.65)
    const gold = rnd() > 0.82
    x.globalAlpha = a
    x.fillStyle = gold ? "#F2D79B" : "#E2E5E8"
    for (const [ox, oy] of [[0, 0], [size, 0], [0, size], [size, size]]) {
      if (px + ox > size * 1.2 || py + oy > size * 1.2) continue
      x.beginPath(); x.arc(px + ox - size, py + oy - size, r, 0, 6.2832); x.fill()
    }
  }
  x.globalAlpha = 1
  const t = Texture.from(c)
  cache.set(key, t)
  return t
}

/** 径向辉光（星云团 / 光池 / 引擎光） */
export function radialGlow(rgb: string, size = 256): Texture {
  const key = `glow-${rgb}-${size}`
  const hit = cache.get(key); if (hit) return hit
  const { c, x } = canvas(size)
  const g = x.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2)
  g.addColorStop(0, `rgba(${rgb},1)`)
  g.addColorStop(0.45, `rgba(${rgb},0.35)`)
  g.addColorStop(1, `rgba(${rgb},0)`)
  x.fillStyle = g; x.fillRect(0, 0, size, size)
  const t = Texture.from(c)
  cache.set(key, t)
  return t
}

/** 远景行星：本体 + 大气层 + 受光侧轮廓光 */
export function planetTexture(size = 512): Texture {
  const key = `planet-${size}`
  const hit = cache.get(key); if (hit) return hit
  const { c, x } = canvas(size)
  const cx = size / 2, cy = size / 2, R = size * 0.42
  // 大气
  const atmo = x.createRadialGradient(cx, cy, R * 0.9, cx, cy, size / 2)
  atmo.addColorStop(0, "rgba(216,163,60,0.30)")
  atmo.addColorStop(0.5, "rgba(216,163,60,0.07)")
  atmo.addColorStop(1, "rgba(216,163,60,0)")
  x.fillStyle = atmo; x.fillRect(0, 0, size, size)
  // 本体（左上受光）
  const body = x.createRadialGradient(cx - R * 0.42, cy - R * 0.46, R * 0.05, cx, cy, R)
  body.addColorStop(0, "rgba(44,52,62,1)")
  body.addColorStop(0.45, "rgba(20,25,32,1)")
  body.addColorStop(1, "rgba(4,5,6,1)")
  x.beginPath(); x.arc(cx, cy, R, 0, 6.2832); x.fillStyle = body; x.fill()
  // 受光侧轮廓光
  x.save()
  x.beginPath(); x.arc(cx, cy, R, 0, 6.2832); x.clip()
  const rim = x.createLinearGradient(cx - R * 0.9, cy - R * 1.0, cx + R * 0.2, cy - R * 0.2)
  rim.addColorStop(0, "rgba(233,190,105,0.55)")
  rim.addColorStop(1, "rgba(233,190,105,0)")
  x.strokeStyle = rim; x.lineWidth = R * 0.05
  x.beginPath(); x.arc(cx, cy, R * 0.99, 0, 6.2832); x.stroke()
  x.restore()
  const t = Texture.from(c)
  cache.set(key, t)
  return t
}

/** 1×1 白点：用于把任意容器当纯色块（省一个 Graphics） */
export function whitePixel(): Texture {
  const hit = cache.get("px"); if (hit) return hit
  const { c, x } = canvas(2)
  x.fillStyle = "#fff"; x.fillRect(0, 0, 2, 2)
  const t = Texture.from(c)
  cache.set("px", t)
  return t
}
