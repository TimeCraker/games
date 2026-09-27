/**
 * 星域突围 · 模拟核心类型（纯数据契约）
 *
 * 红线：本目录（sim/）**不得** import React / Pixi / window / document。
 * 内容层（content/）与渲染层（render/）、UI 层（ui/）都只依赖这里的类型。
 */

export type WeaponKind = "melee" | "ranged" | "field"

export type WeaponId =
  // 近战
  | "ram" | "blade" | "hook" | "edge"
  // 远程
  | "scatter" | "missile" | "sniper"
  // 法术（引力 / 空间场）
  | "well" | "repulse" | "rift"

export type ClassId = "brawler" | "gunner" | "gravity" | "tank" | "skirmisher"

export type ESkillId = "blink" | "shield" | "afterburn" | "recharge" | "quantum"

export type EnemyKind = "scout" | "drone" | "heavy" | "boss"

export type Vec = { x: number; y: number }

export type Rect = { x: number; y: number; w: number; h: number; rot?: number }

/** 单把武器的当局状态 */
export type WeaponSlot = {
  id: WeaponId
  stars: number
  /** 用于三合一的同名同星计数（0..2），满 3 即自动合成升星 */
  mergeCount: number
  cooldown: number
}

export type PlayerState = {
  x: number; y: number; vx: number; vy: number
  hp: number; maxHp: number; r: number
  invuln: number
  facing: number
  /** 护盾剩余时间（E 技） */
  shield: number
  /** 量子回跳记录的坐标（null = 未记录） */
  quantumMark: Vec | null
}

export type EnemyState = {
  id: number
  kind: EnemyKind
  x: number; y: number; vx: number; vy: number
  hp: number; maxHp: number; r: number
  speed: number
  dmg: number
  /** 被引力井吸附的强度（0 = 无） */
  pull: number
  /** 接触伤害间隔计时（内部用） */
  touchCd: number
  /** 远程敌人开火计时（内部用） */
  shootCd: number
}

export type BulletState = {
  id: number
  x: number; y: number; vx: number; vy: number
  r: number; dmg: number; life: number
  pierce: number
  hit: number[]
}

export type EnemyShotState = {
  id: number
  x: number; y: number; vx: number; vy: number
  r: number; dmg: number; life: number
}

/** 法术场（引力井 / 斥力波 / 空间裂缝） */
export type FieldState = {
  id: number
  weapon: WeaponId
  x: number; y: number; r: number
  life: number; maxLife: number
  dmgPerSec: number
  pull: number
}

export type DropKind = "coin" | "xp" | "health" | "weapon"

export type DropState = {
  id: number
  kind: DropKind
  x: number; y: number; vx: number; vy: number
  value: number
  /** kind === "weapon" 时携带的武器 id */
  weapon?: WeaponId
  t: number
}

export type ParticleState = {
  x: number; y: number; vx: number; vy: number
  life: number; maxLife: number; size: number
  kind: "spark" | "shard" | "smoke"
  color: number
}

/** 模拟 → 渲染/音效的单向事件（不改任何模拟数值） */
export type SimEvent =
  | { type: "shoot"; x: number; y: number; ang: number; kind: WeaponKind }
  | { type: "hit"; x: number; y: number; amount: number; crit: boolean }
  | { type: "kill"; x: number; y: number; kind: EnemyKind }
  | { type: "pickup"; x: number; y: number; kind: DropKind }
  | { type: "merge"; x: number; y: number; weapon: WeaponId; stars: number }
  | { type: "levelup"; level: number }
  | { type: "hurt"; x: number; y: number; amount: number }
  | { type: "eskill"; x: number; y: number; id: ESkillId }
  | { type: "death" }
  | { type: "wave"; wave: number }

export type RunPhase = "hangar" | "run" | "shop" | "dead"

export type RunStats = {
  kills: number
  score: number
  coins: number
  level: number
  time: number
  wave: number
  dps: number
}
