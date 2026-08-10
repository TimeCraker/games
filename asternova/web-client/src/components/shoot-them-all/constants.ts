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

/**
 * 物理参数（Stage Spec §3.2/§3.3/§3.5/§3.7/§3.10）。
 * 引擎层与渲染层共享；引擎层零 React/Pixi 依赖。
 */
export const PHYS = {
  // Engine
  gravityY: 1.15,
  fixedDelta: 1000 / 60, // 16.667ms，固定步长
  positionIterations: 8,
  velocityIterations: 8,
  constraintIterations: 4,
  // 陨星（标准）
  ballRadius: 9,
  ballRestitution: 0.55, // 核心修复：旧版 0.98 → 0.55
  ballFriction: 0.001,
  ballFrictionAir: 0.006,
  ballDensity: 0.005,
  ballSlop: 0.02,
  // 星象仪（发射器）
  launchAnchor: { x: 360, y: 70 },
  angleMax: (78 * Math.PI) / 180, // ±78°
  v0: 14, // 初速度 px/step
  vMax: 16, // 速度钳制（防穿透：16 < 球9+钉10=19）
  // 普通晶体钉
  pegRadius: 10,
  pegRestitution: 0.5,
} as const
