import type { WeaponId, WeaponKind } from "../sim/types"

/**
 * 武器池 · 全局 10 把（白皮书 §5.1）
 * 近战 4 / 远程 3 / 法术 3；每职业只取其中 3 把（见 classes.ts）。
 *
 * 升星规则（白皮书 §5.3）：只加伤害与射程/范围，**不引入随机词条**。
 */
export type WeaponDef = {
  id: WeaponId
  name: string
  kind: WeaponKind
  /** 一句话区分（简报/商店用） */
  blurb: string
  /** 基础伤害 */
  dmg: number
  /** 每升 1 星的伤害倍率（线性叠加：dmg * (1 + starScale*(stars-1))） */
  starScale: number
  /** 开火/生效间隔（秒） */
  cd: number
  /** 射程（远程=弹道寿命换算；近战=挥击半径；法术=场半径） */
  range: number
  /** 每星射程增量 */
  rangePerStar: number
  /** 远程：弹速；近战：挥击张角；法术：场持续 */
  speed: number
  /** 远程穿透次数 */
  pierce: number
  /** 法术场每秒伤害系数（相对 dmg） */
  dpsMul?: number
  /** 法术场吸附强度 */
  pull?: number
}

export const WEAPONS: Record<WeaponId, WeaponDef> = {
  // ── 近战：船头撞角 / 回旋刃 / 牵引钩 / 快刀 ──
  ram:     { id: "ram",     name: "冲角",     kind: "melee", blurb: "舰装前突硬撞，击退并造成高额单次伤害", dmg: 26, starScale: 0.45, cd: 0.95, range: 92,  rangePerStar: 10, speed: 1.4,  pierce: 99 },
  blade:   { id: "blade",   name: "回旋刃",   kind: "melee", blurb: "绕船环绕的旋转刃，持续切割近身敌人", dmg: 9,  starScale: 0.40, cd: 0.30, range: 78,  rangePerStar: 8,  speed: 3.1,  pierce: 99 },
  hook:    { id: "hook",    name: "牵引钩",   kind: "melee", blurb: "勾住并把敌人拽向自己，打断冲锋节奏",   dmg: 15, starScale: 0.42, cd: 1.15, range: 148, rangePerStar: 14, speed: 0.9,  pierce: 3 },
  edge:    { id: "edge",    name: "快刀",     kind: "melee", blurb: "极短间隔的贴身快斩，吃走位与贴脸",   dmg: 7,  starScale: 0.38, cd: 0.16, range: 56,  rangePerStar: 5,  speed: 3.6,  pierce: 99 },

  // ── 远程：弹道直射 ──
  scatter: { id: "scatter", name: "散射炮",   kind: "ranged", blurb: "一次打出多枚弹丸，近距离覆盖强",     dmg: 8,  starScale: 0.34, cd: 0.62, range: 520, rangePerStar: 26, speed: 520, pierce: 0 },
  missile: { id: "missile", name: "追踪导弹", kind: "ranged", blurb: "自动转向追踪最近目标，适合清散兵",   dmg: 17, starScale: 0.46, cd: 1.05, range: 640, rangePerStar: 30, speed: 340, pierce: 0 },
  sniper:  { id: "sniper",  name: "穿透狙击", kind: "ranged", blurb: "高伤直线弹，可贯穿一整列敌人",       dmg: 34, starScale: 0.55, cd: 1.35, range: 900, rangePerStar: 40, speed: 900, pierce: 6 },

  // ── 法术：在地/空间放一个场（不是「子弹飞过去」） ──
  well:    { id: "well",    name: "引力井",   kind: "field", blurb: "制造引力场，把敌人聚拢并持续绞杀", dmg: 12, starScale: 0.40, cd: 3.4, range: 130, rangePerStar: 12, speed: 2.6, pierce: 0, dpsMul: 1.0, pull: 150 },
  repulse: { id: "repulse", name: "斥力波",   kind: "field", blurb: "以自身为中心向外炸开，推开并致伤", dmg: 22, starScale: 0.44, cd: 3.0, range: 190, rangePerStar: 16, speed: 0.9, pierce: 0, dpsMul: 1.4, pull: -260 },
  rift:    { id: "rift",    name: "空间裂缝", kind: "field", blurb: "定点撕开裂缝，长时间持续掉血",     dmg: 16, starScale: 0.42, cd: 3.8, range: 108, rangePerStar: 10, speed: 4.2, pierce: 0, dpsMul: 1.2, pull: 40 },
}

export const WEAPON_IDS = Object.keys(WEAPONS) as WeaponId[]

/** 升星后的实际伤害 */
export function weaponDamage(def: WeaponDef, stars: number): number {
  return def.dmg * (1 + def.starScale * (stars - 1))
}
/** 升星后的实际射程/半径 */
export function weaponRange(def: WeaponDef, stars: number): number {
  return def.range + def.rangePerStar * (stars - 1)
}

/** 三合一：3 个同名同星 → +1 星 */
export const MERGE_REQUIRED = 3
export const MAX_STARS = 5
/** 直接花钱升 1 星的基础价（随当前星级递增） */
export function upgradeCost(stars: number): number {
  return Math.round(60 * Math.pow(1.85, Math.max(0, stars - 1)))
}
