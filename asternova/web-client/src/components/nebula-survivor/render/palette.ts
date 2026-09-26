/**
 * Nebula Survivor — Pixi 渲染层 · 色板与工具函数
 * 视觉方向：终末地 / 崩铁式（冷峻赛璐璐 + 深空玻璃 + 克制紫青点缀）
 * 功能色语义对齐 shoot-them-all/constants.ts 的 PALETTE。
 */

/** 深空背景三段（冷蓝紫，非纯黑） */
export const NB_BG = {
  top: 0x141130,
  mid: 0x0c0a24,
  bot: 0x050514,
} as const

/** 游戏内物体功能色（hex int，供 Pixi Graphics.fill 使用） */
export const NEBULA = {
  // 友方 / 玩家 / 能量（冷青）
  azurite: 0x5ac8f0,
  iceWhite: 0xd7ecff,
  hullDark: 0x10243a,

  // 玩家激光弹（延续粉红弹幕身份）
  laserCore: 0xfff3fb,
  laserMid: 0xff6eb4,
  laserOuter: 0xc05ae0,

  // 星环粒子（冰白 + 冷青）
  orbCore: 0xffffff,
  orbFrost: 0xd4ecff,

  // 敌人（危险色，分档）
  enemy1: 0xff8a5c,
  enemy1rim: 0xffd7ba,
  enemy2: 0xc465ff,
  enemy2rim: 0xecc8ff,
  enemy3: 0xff5fc3,
  enemy3rim: 0xffd9f4,

  // XP 结晶（粉紫，延续「掉落物」认知）
  crystalCore: 0xfff0ff,
  crystalMid: 0xff9ae8,
  crystalOuter: 0xc461f0,

  // 急救包（青绿 + 十字）
  heal: 0x34d399,
  healCore: 0xd9fff0,
} as const

/** mulberry32 确定性 PRNG —— 背景星点/星云布局稳定 */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t
}

export function lerpColor(c1: number, c2: number, t: number): number {
  const r = Math.round(lerp((c1 >> 16) & 0xff, (c2 >> 16) & 0xff, t))
  const g = Math.round(lerp((c1 >> 8) & 0xff, (c2 >> 8) & 0xff, t))
  const b = Math.round(lerp(c1 & 0xff, c2 & 0xff, t))
  return (r << 16) | (g << 8) | b
}

export const TAU = Math.PI * 2
