import type { ClassId, ESkillId, WeaponId } from "../sim/types"

/**
 * 机型 = 舰装少女的装配方案（白皮书 §4）：数值倾向 + 专属武器（3 把） + 专属 E 技。
 *
 * 设定（2026-09-27 制作人拍板）：玩家是**人形本体 + 可换装舰装挂架**，不是匿名战舰。
 * 因此这里叫「机型」而非「舰种」—— 本体是角色，舰装是可收集/可替换的装备。
 */
export type ClassDef = {
  id: ClassId
  name: string
  /** 一行的调性说明 */
  role: string
  maxHp: number
  /** 世界单位/秒 */
  speed: number
  /** 全局伤害倍率（近战/远程/法术通吃） */
  dmgMul: number
  /** 法术额外倍率（引力型专属倾向） */
  spellMul: number
  /** 减伤（0..0.6） */
  armor: number
  weapons: [WeaponId, WeaponId, WeaponId]
  eskill: ESkillId
  /** 三向倾向刻度 0..1，仅用于机库界面展示 */
  traits: [number, number, number]
}

export const CLASSES: Record<ClassId, ClassDef> = {
  brawler: {
    id: "brawler", name: "近卫型", role: "高攻高防 · 贴脸绞杀",
    maxHp: 130, speed: 236, dmgMul: 1.15, spellMul: 1.0, armor: 0.20,
    weapons: ["ram", "blade", "hook"], eskill: "blink", traits: [0.55, 0.85, 0.70],
  },
  gunner: {
    id: "gunner", name: "炮击型", role: "高攻低防 · 中远压制",
    maxHp: 92, speed: 250, dmgMul: 1.26, spellMul: 1.0, armor: 0.05,
    weapons: ["scatter", "missile", "sniper"], eskill: "afterburn", traits: [0.62, 0.95, 0.42],
  },
  gravity: {
    id: "gravity", name: "引力型", role: "高法低物防 · 场控",
    maxHp: 96, speed: 240, dmgMul: 1.06, spellMul: 1.45, armor: 0.08,
    weapons: ["well", "repulse", "rift"], eskill: "shield", traits: [0.50, 0.88, 0.55],
  },
  tank: {
    id: "tank", name: "重装型", role: "超高防 · 慢速推进",
    maxHp: 178, speed: 198, dmgMul: 0.86, spellMul: 1.0, armor: 0.38,
    weapons: ["ram", "hook", "blade"], eskill: "recharge", traits: [0.22, 0.58, 0.98],
  },
  skirmisher: {
    id: "skirmisher", name: "机动型", role: "高机动高爆 · 脆",
    maxHp: 78, speed: 322, dmgMul: 1.32, spellMul: 1.0, armor: 0.02,
    weapons: ["edge", "blade", "hook"], eskill: "quantum", traits: [0.96, 0.80, 0.30],
  },
}

export const CLASS_IDS = Object.keys(CLASSES) as ClassId[]
export const DEFAULT_CLASS: ClassId = "brawler"
