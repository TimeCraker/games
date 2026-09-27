import type { ESkillId } from "../sim/types"

/** E 主动技（白皮书 §6）：纯走位/生存向，无输出型 */
export type ESkillDef = {
  id: ESkillId
  name: string
  blurb: string
  /** 冷却（秒） */
  cd: number
  /** 通用时长参数（护盾时长 / 加速时长 / 无敌帧） */
  duration?: number
  /** 位移距离（闪现）/ 移动倍率（尾焰） / 治疗量（充能） */
  amount?: number
}

export const ESKILLS: Record<ESkillId, ESkillDef> = {
  blink:     { id: "blink",     name: "闪现",     blurb: "向移动方向短距瞬移，带极短无敌帧", cd: 6.5,  amount: 190, duration: 0.25 },
  shield:    { id: "shield",    name: "护盾",     blurb: "短时吸收全部伤害",                 cd: 15.0, duration: 3.6 },
  afterburn: { id: "afterburn", name: "尾焰疾驰", blurb: "短时大幅提速并留下尾迹",           cd: 10.0, duration: 3.6, amount: 1.8 },
  recharge:  { id: "recharge",  name: "装甲充能", blurb: "立刻回复大幅结构值",               cd: 18.0, amount: 38 },
  quantum:   { id: "quantum",   name: "量子回跳",  blurb: "按一下记录位置，再按一下瞬移回去", cd: 0.6 },
}

export const ESKILL_IDS = Object.keys(ESKILLS) as ESkillId[]
