/**
 * Nebula Survivor — Pixi 渲染层 · 色板与工具函数
 * 视觉方向：AsterNova 品牌色（冷中性黑底 + 单一琥珀主色 + 青柠苔绿副色 + 信号色）
 * 硬约束：禁用紫 / 品红 / 紫罗兰与高饱和青蓝（AI 味来源）。
 * 功能色语义对齐 shoot-them-all/constants.ts 的 PALETTE。
 */

/** 深空背景三段（冷中性黑，无紫相） */
export const NB_BG = {
  top: 0x0b0d12,
  mid: 0x08090d,
  bot: 0x050608,
} as const

/** 游戏内物体功能色（hex int，供 Pixi Graphics.fill 使用） */
export const NEBULA = {
  // 友方 / 玩家 / 能量（品牌主色 · 琥珀）
  azurite: 0xd8a33c,
  iceWhite: 0xf2d79b,
  hullDark: 0x111316,

  // 玩家激光弹（琥珀金弹幕）
  laserCore: 0xfff6e2,
  laserMid: 0xe9be69,
  laserOuter: 0x8a6519,

  // 星环粒子（暖白 + 琥珀）
  orbCore: 0xffffff,
  orbFrost: 0xf2d79b,

  // 敌人（危险色，分档：珊瑚 / 翠玉 / 信号红）
  enemy1: 0xc08069,
  enemy1rim: 0xe8cbb8,
  enemy2: 0x7fb39e,
  enemy2rim: 0xcfe8de,
  enemy3: 0xc0503a,
  enemy3rim: 0xe0a99b,

  // XP 结晶（琥珀金，延续「掉落物」认知）
  crystalCore: 0xfff6e2,
  crystalMid: 0xd8a33c,
  crystalOuter: 0x8a6519,

  // 急救包（品牌成功色 + 十字）
  heal: 0x4f8d6b,
  healCore: 0xcfe8de,
} as const

/** 赛璐璐三色调 + 深描边（终末地式：平涂 base + 阴影调 shadow + 亮面 hi + 描边 outline） */
export const TONES = {
  player: { base: 0xd8a33c, shadow: 0x8a6519, hi: 0xfff6e2, outline: 0x3a2a08 },
  enemy1: { base: 0xc08069, shadow: 0x7e4a38, hi: 0xe8cbb8, outline: 0x3a1a10 },
  enemy2: { base: 0x7fb39e, shadow: 0x4e7d6a, hi: 0xcfe8de, outline: 0x1c3830 },
  enemy3: { base: 0xc0503a, shadow: 0x8a3423, hi: 0xe0a99b, outline: 0x40140c },
  crystal: { base: 0xd8a33c, shadow: 0x8a6519, hi: 0xfff6e2, outline: 0x3a2a08 },
  heal: { base: 0x4f8d6b, shadow: 0x2f5c45, hi: 0xcfe8de, outline: 0x11291e },
  bullet: { base: 0xfff6e2, shadow: 0xe9be69, hi: 0xffffff, outline: 0x6b4a10 },
  orb: { base: 0xffffff, shadow: 0xf2d79b, hi: 0xffffff, outline: 0x6b4a10 },
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
