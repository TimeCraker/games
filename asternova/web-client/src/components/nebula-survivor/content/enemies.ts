import type { EnemyKind } from "../sim/types"

/** 敌方档位：三档小怪 + 每局一个 Boss（白皮书 §7） */
export type EnemyDef = {
  kind: EnemyKind
  name: string
  hp: number
  r: number
  speed: number
  dmg: number
  /** 接触伤害间隔（秒） */
  touchCd: number
  /** 掉落 */
  coin: number
  xp: number
  score: number
  /** 是否远程（会朝玩家开火） */
  shooter?: boolean
}

export const ENEMIES: Record<EnemyKind, EnemyDef> = {
  scout: { kind: "scout", name: "游猎机", hp: 24,  r: 13, speed: 96, dmg: 8,  touchCd: 0.7, coin: 3,  xp: 4,  score: 10 },
  drone: { kind: "drone", name: "蜂群机", hp: 48,  r: 16, speed: 78, dmg: 12, touchCd: 0.8, coin: 6,  xp: 7,  score: 22, shooter: true },
  heavy: { kind: "heavy", name: "重甲机", hp: 128, r: 22, speed: 54, dmg: 20, touchCd: 1.0, coin: 14, xp: 15, score: 55 },
  boss:  { kind: "boss",  name: "母舰核心", hp: 2600, r: 46, speed: 46, dmg: 34, touchCd: 1.2, coin: 260, xp: 240, score: 900, shooter: true },
}

export const ENEMY_KINDS = Object.keys(ENEMIES) as EnemyKind[]
