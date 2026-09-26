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
 * 街机统一色板 —— 与 app/globals.css 的 --amber-* / --ink-* / --arcade-* 对齐。
 *
 * 2026-09-27 换色：原表以 azurite(青) 为主色，另用 violet/cyan 画星云与扫描线，
 * 实测在近乎空白的画布上呈现为「深蓝 + 青 + 紫」——正是主站已清除的 AI 味组合，
 * 与冷黑 + 琥珀的品牌体系不符（Stage Spec §6.1 的三色锚点在此作废，以本条为准）。
 *
 * 角色分工：琥珀 = 玩家/能量/奖励（品牌主色）；翠玉 = 普通晶体（本游戏副色）；
 * 信号红 = 危险；信号绿 = 治疗/过关；冷灰 = 中性描边。
 */
export const PALETTE = {
  /** 玩家 / 发射器 / 陨星 / 能量 / 奖励（品牌主色） */
  amber: 0xd8a33c,
  amberBright: 0xe9be69,
  amberPale: 0xf2d79b,
  /** 普通晶体（本游戏副色：翠玉） */
  jade: 0x7fb39e,
  jadeLight: 0xcfe8de,
  /** 危险 / 敌人 / 伤害（信号色） */
  danger: 0xc0503a,
  /** 治疗 / 过关（信号色） */
  life: 0x4f8d6b,
  /** 中性描边（冷灰，替代原淡蓝 0xc7ecff） */
  line: 0x8c949e,
} as const

/** 深空背景 L0 三段垂直渐变（冷中性黑，已去紫相） */
export const BG_GRADIENT = {
  top: 0x08090d,
  mid: 0x0b0d12,
  bot: 0x050608,
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