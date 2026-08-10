/**
 * Shoot Them All v2 — 全局常量
 *
 * 物理弹射肉鸽（Physics-Bounce Roguelite）· 星海星云身份。
 * 数值来源：Stage Spec §3.10 物理数值总表 / §6.1 色彩系统。
 * 引擎层（engine/）与渲染层（render/）共享本文件，零 React/Pixi 依赖。
 */

/** 逻辑画布：纵向 720×1280（Stage Spec §3.1，纵向适配顶射角度发射 + 移动端竖屏） */
export const WIDTH = 720
export const HEIGHT = 1280

/**
 * 星海星云三色锚点（Stage Spec §6.1）—— 游戏内物体功能色。
 * 紫色（violet）只做 UI 专属，游戏内物体层退出紫粉色域。
 */
export const PALETTE = {
  azurite: 0x5ac8f0, // 友方 / 玩家 / 能量（球、发射器、HP、普通晶体）
  amber: 0xf5b83a, // 暴击 / 奖励 / 弱点（共鸣核心、遗物稀有度金）
  magenta: 0xe8445f, // 危险 / 敌人 / 伤害（敌人本体、伤害数字、Boss）
  emerald: 0x34d399, // 治疗 / 过关 / 生命星云
  violet: 0xa855f7, // UI 专属（按钮 / focus / 玻璃描边）
  cyan: 0x38bdf8, // UI 次级强调
} as const

/** 深空背景 L0 三段垂直渐变（hex 近似 Stage Spec §6.2 的 oklch） */
export const BG_GRADIENT = {
  top: 0x080912,
  mid: 0x0e1130,
  bot: 0x05060f,
} as const
