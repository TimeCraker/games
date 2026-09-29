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
 * 玩法规则数值（白皮书 §4/§5/§7）。
 * 都是「首发放个像样的数」，实测后再调 —— 集中放这里避免散落各处。
 */
export const RULES = {
  /** 钉基础分：晶体 100 / 共鸣 150 / 炸弹钉（预留） */
  pegScore: { crystal: 100, resonance: 150, bomb: 200 },
  /** 障碍击碎奖励（少量分） */
  obstacleScore: 80,
  /**
   * 连击加成：同一次出手内第 n 颗钉 ×(1 + 0.1*(n-1))，封顶 2×。
   * 例：第 1 颗 ×1.0、第 2 颗 ×1.1 … 第 11 颗起恒 ×2.0。
   */
  comboStep: 0.1,
  comboCap: 2,
  /** 爆裂弹清场半径（px，白皮书「~90px」） */
  blastRadius: 90,
  /** 每次命中对钉的伤害（heavy 高伤，可秒大钉 hp=2） */
  pegDamage: { standard: 1, blast: 1, pierce: 1, heavy: 2 },
  /** 仅 heavy 对障碍造成伤害（其他球碰障碍只弹开） */
  heavyObstacleDamage: 2,
  /** 球落定/出界后到下一球的短暂停顿（ms，留给 UI 播反馈） */
  resolveMs: 400,
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

/**
 * 球种手感分化（2026-09-28 数值实测调优，遗留风险 #3）。
 *
 * 语义目标：heavy「更沉」= 低弹+微抓地+高密度，撞上去像夯一下；
 * pierce「更飘快」= 零风阻+轻质+更滑，穿阵时贴直线滑过去；
 * blast「更猛」= 高弹+低风阻，爆完还带着劲乱窜。
 *
 * ⚠️ 镜像红线：GameEngine.launch（实弹）与 GhostPredictor.predict（幽灵球）
 * 必须经由同一 applyBallPhys 施加本表，逐条一致才保 <2px 轨迹精度。
 * 另注：matter 弹性合成 = max(球, 钉)，故 restitution 差异在碰钉时有效
 * （钉 0.5 → heavy 合成 0.50 / standard 0.55 / blast 0.62）；
 * 而 setStatic(false) 会用 _original 快照还原 restitution/friction/density，
 * 施加必须发生在 setStatic(false) 之后（见 launch）。
 */
export const BALL_PHYS = {
  /** 基准（白皮书 §7：restitution 0.55） */
  standard: { restitution: 0.55, friction: 0.001, frictionAir: 0.006, density: 0.005 },
  /** 重弹「更沉」：钝弹、贴障碍、质量感 */
  heavy: { restitution: 0.5, friction: 0.004, frictionAir: 0.006, density: 0.008 },
  /** 穿透弹「更飘快」：零风阻（穿钉不衰减）+ 轻质 */
  pierce: { restitution: 0.6, friction: 0.0005, frictionAir: 0, density: 0.0035 },
  /** 爆裂弹「更猛】：高弹 + 低风阻 */
  blast: { restitution: 0.62, friction: 0.001, frictionAir: 0.004, density: 0.0055 },
} as const