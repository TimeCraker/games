import type { LevelDef, ObstacleSpec, PegKind, PegSpec } from "../types"

/**
 * 关卡内容（白皮书 §5/§6）：首发 10 关，逐关引入球种/障碍/特殊钉。
 *
 * 布局约定（720×1280 纵向画布）：
 * - 钉阵在中下部 y ∈ [380, 1150]；顶部 y < 200 留给发射器与 HUD。
 * - 钉间距 ≥ 2.2×pegRadius（=22px），防止球卡进钉缝（2026-09-27 物理口径）。
 *   实际构图按 40px+ 走，给弹跳留呼吸感。
 * - 每关手写构图意图（星环/回廊/星簇/门关/长廊/护盾/矩阵/斜径/堡垒/终章），
 *   不做「同一簇换皮」——新鲜感靠板面布局本身。
 *
 * 坐标为手写构图，改数值时用「布局辅助函数」保持对称性。
 */

// ---- 布局辅助（只做对称阵列的坐标展开，不含任何玩法逻辑）----

function row(y: number, x0: number, x1: number, n: number, kind: PegKind, hp = 1): PegSpec[] {
  const out: PegSpec[] = []
  for (let i = 0; i < n; i++) {
    const x = n === 1 ? (x0 + x1) / 2 : x0 + ((x1 - x0) * i) / (n - 1)
    out.push({ x, y, kind, hp })
  }
  return out
}

function col(x: number, y0: number, y1: number, n: number, kind: PegKind, hp = 1): PegSpec[] {
  const out: PegSpec[] = []
  for (let i = 0; i < n; i++) {
    const y = n === 1 ? (y0 + y1) / 2 : y0 + ((y1 - y0) * i) / (n - 1)
    out.push({ x, y, kind, hp })
  }
  return out
}

/** 圆环阵：phaseDeg=-90 使首钉在正上方（屏幕坐标 y 向下） */
function ring(cx: number, cy: number, r: number, n: number, kind: PegKind, phaseDeg = -90, hp = 1): PegSpec[] {
  const out: PegSpec[] = []
  for (let i = 0; i < n; i++) {
    const a = ((phaseDeg + (360 * i) / n) * Math.PI) / 180
    out.push({ x: cx + r * Math.cos(a), y: cy + r * Math.sin(a), kind, hp })
  }
  return out
}

/** 圆弧阵：[deg0, deg1] 均分 n 点（含两端） */
function arc(cx: number, cy: number, r: number, deg0: number, deg1: number, n: number, kind: PegKind, hp = 1): PegSpec[] {
  const out: PegSpec[] = []
  for (let i = 0; i < n; i++) {
    const a = ((deg0 + ((deg1 - deg0) * i) / (n - 1)) * Math.PI) / 180
    out.push({ x: cx + r * Math.cos(a), y: cy + r * Math.sin(a), kind, hp })
  }
  return out
}

/** 矩形阵列（cols×rows，间距 dx/dy），左上角锚定 */
function grid(x0: number, y0: number, cols: number, rows: number, dx: number, dy: number, kind: PegKind, hp = 1): PegSpec[] {
  const out: PegSpec[] = []
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      out.push({ x: x0 + c * dx, y: y0 + r * dy, kind, hp })
    }
  }
  return out
}

// ---- 10 关手写构图 ----

/** L1 星环序曲：双层星环弧 + 底部三星。教学关，全标准弹 + 普通钉。 */
const L1_PEGS: PegSpec[] = [
  ...arc(360, 480, 200, 25, 155, 9, "crystal"),
  ...arc(360, 540, 280, 35, 145, 11, "crystal"),
  { x: 360, y: 980, kind: "crystal", hp: 1 },
  { x: 300, y: 1040, kind: "crystal", hp: 1 },
  { x: 420, y: 1040, kind: "crystal", hp: 1 },
]

/** L2 共鸣回廊：左右晶体墙夹共鸣主轴，上下弧封口。引入共鸣钉。 */
const L2_PEGS: PegSpec[] = [
  ...col(170, 430, 970, 8, "crystal"),
  ...col(550, 430, 970, 8, "crystal"),
  ...col(360, 480, 920, 6, "resonance"),
  ...arc(360, 580, 170, 210, 330, 7, "crystal"),
  ...arc(360, 860, 170, 30, 150, 7, "crystal"),
  { x: 265, y: 700, kind: "resonance", hp: 1 },
  { x: 455, y: 700, kind: "resonance", hp: 1 },
]

/** L3 爆裂星簇：中央密集簇（爆裂弹主场）+ 外围共鸣环 + 四角散钉。 */
const L3_PEGS: PegSpec[] = [
  ...grid(255, 600, 5, 4, 60, 60, "crystal"),
  ...ring(360, 700, 250, 8, "resonance"),
  { x: 150, y: 420, kind: "crystal", hp: 1 },
  { x: 570, y: 420, kind: "crystal", hp: 1 },
  { x: 360, y: 420, kind: "crystal", hp: 1 },
  { x: 150, y: 1020, kind: "crystal", hp: 1 },
  { x: 570, y: 1020, kind: "crystal", hp: 1 },
  { x: 360, y: 1100, kind: "crystal", hp: 1 },
]

/** L4 石阵门关：两根石柱 + 顶横梁构成「门」，门内藏共鸣主轴（重弹主场）。 */
const L4_OBSTACLES: ObstacleSpec[] = [
  { x: 200, y: 640, w: 44, h: 230, kind: "stone", hp: 2 },
  { x: 520, y: 640, w: 44, h: 230, kind: "stone", hp: 2 },
  { x: 360, y: 480, w: 280, h: 36, kind: "stone", hp: 2 },
]
const L4_PEGS: PegSpec[] = [
  ...col(360, 600, 900, 4, "resonance"),
  ...col(110, 560, 920, 5, "crystal"),
  ...col(610, 560, 920, 5, "crystal"),
  ...row(560, 280, 440, 3, "resonance"),
  ...row(400, 120, 240, 3, "crystal"),
  ...row(400, 480, 600, 3, "crystal"),
  ...row(1000, 240, 480, 5, "crystal"),
  ...row(1080, 240, 480, 5, "crystal"),
]

/** L5 穿晶长廊：三列长钉阵（穿透弹直线清一串）+ 上下横排 + 侧翼共鸣。 */
const L5_PEGS: PegSpec[] = [
  ...col(180, 460, 1060, 8, "crystal"),
  ...col(360, 460, 1060, 8, "resonance"),
  ...col(540, 460, 1060, 8, "crystal"),
  ...row(400, 240, 480, 5, "crystal"),
  ...row(1120, 240, 480, 5, "crystal"),
  { x: 270, y: 560, kind: "resonance", hp: 1 },
  { x: 450, y: 560, kind: "resonance", hp: 1 },
  { x: 270, y: 960, kind: "resonance", hp: 1 },
  { x: 450, y: 960, kind: "resonance", hp: 1 },
]

/** L6 冰环护盾：三层同心环 + 四角冰护盾（冰需重弹破）。 */
const L6_OBSTACLES: ObstacleSpec[] = [
  { x: 105, y: 465, w: 80, h: 24, kind: "ice", hp: 1 },
  { x: 615, y: 465, w: 80, h: 24, kind: "ice", hp: 1 },
  { x: 105, y: 975, w: 80, h: 24, kind: "ice", hp: 1 },
  { x: 615, y: 975, w: 80, h: 24, kind: "ice", hp: 1 },
]
const L6_PEGS: PegSpec[] = [
  ...ring(360, 720, 130, 8, "resonance"),
  ...ring(360, 720, 190, 8, "crystal"),
  ...ring(360, 720, 250, 12, "crystal"),
  ...row(400, 240, 480, 5, "crystal"),
  ...row(1040, 240, 480, 5, "crystal"),
  ...col(70, 620, 820, 3, "crystal"),
  ...col(650, 620, 820, 3, "crystal"),
]

/** L7 菱光矩阵：中央菱形晶格 + 双侧石柱 + 底梁，共鸣嵌在菱心。 */
const L7_OBSTACLES: ObstacleSpec[] = [
  { x: 135, y: 720, w: 36, h: 170, kind: "stone", hp: 2 },
  { x: 585, y: 720, w: 36, h: 170, kind: "stone", hp: 2 },
  { x: 360, y: 1020, w: 220, h: 36, kind: "stone", hp: 2 },
  { x: 200, y: 1020, w: 70, h: 24, kind: "ice", hp: 1 },
  { x: 520, y: 1020, w: 70, h: 24, kind: "ice", hp: 1 },
]
const L7_PEGS: PegSpec[] = [
  { x: 360, y: 420, kind: "crystal", hp: 1 },
  ...row(500, 300, 420, 2, "crystal"),
  ...row(580, 240, 480, 3, "crystal"),
  { x: 180, y: 660, kind: "crystal", hp: 1 },
  { x: 300, y: 660, kind: "resonance", hp: 1 },
  { x: 420, y: 660, kind: "resonance", hp: 1 },
  { x: 540, y: 660, kind: "crystal", hp: 1 },
  // 菱腰三钉：两侧晶钉 + 菱心共鸣（不能用 row(740,…3) 再叠一颗 360 的共鸣——坐标撞车）
  { x: 240, y: 740, kind: "crystal", hp: 1 },
  { x: 360, y: 740, kind: "resonance", hp: 1 },
  { x: 480, y: 740, kind: "crystal", hp: 1 },
  ...row(820, 300, 420, 2, "crystal"),
  { x: 360, y: 900, kind: "crystal", hp: 1 },
  ...col(80, 480, 960, 7, "crystal"),
  ...col(640, 480, 960, 7, "crystal"),
  ...col(220, 520, 920, 4, "resonance"),
  ...col(500, 520, 920, 4, "resonance"),
  ...arc(360, 560, 180, 220, 320, 6, "crystal"),
  ...row(1120, 260, 460, 4, "crystal"),
]

/** L8 星瀑斜径：四条斜向晶带 + 两条共鸣斜带，底部冰石收口。 */
const L8_OBSTACLES: ObstacleSpec[] = [
  { x: 150, y: 1120, w: 110, h: 28, kind: "ice", hp: 1 },
  { x: 360, y: 1120, w: 120, h: 28, kind: "stone", hp: 2 },
  { x: 570, y: 1120, w: 110, h: 28, kind: "ice", hp: 1 },
]
const L8_PEGS: PegSpec[] = [
  // 斜带统一方向 (dx=55, dy=85)，四条晶体带 + 两条共鸣带交错
  { x: 50, y: 520, kind: "crystal", hp: 1 },
  { x: 105, y: 605, kind: "crystal", hp: 1 },
  { x: 160, y: 690, kind: "crystal", hp: 1 },
  { x: 215, y: 775, kind: "crystal", hp: 1 },
  { x: 270, y: 860, kind: "crystal", hp: 1 },
  { x: 325, y: 945, kind: "crystal", hp: 1 },
  { x: 185, y: 480, kind: "resonance", hp: 1 },
  { x: 240, y: 565, kind: "resonance", hp: 1 },
  { x: 295, y: 650, kind: "resonance", hp: 1 },
  { x: 350, y: 735, kind: "resonance", hp: 1 },
  { x: 405, y: 820, kind: "resonance", hp: 1 },
  { x: 460, y: 905, kind: "resonance", hp: 1 },
  { x: 515, y: 990, kind: "resonance", hp: 1 },
  { x: 570, y: 1075, kind: "resonance", hp: 1 },
  { x: 120, y: 440, kind: "crystal", hp: 1 },
  { x: 175, y: 525, kind: "crystal", hp: 1 },
  { x: 230, y: 610, kind: "crystal", hp: 1 },
  { x: 285, y: 695, kind: "crystal", hp: 1 },
  { x: 340, y: 780, kind: "crystal", hp: 1 },
  { x: 395, y: 865, kind: "crystal", hp: 1 },
  { x: 450, y: 950, kind: "crystal", hp: 1 },
  { x: 505, y: 1035, kind: "crystal", hp: 1 },
  { x: 315, y: 480, kind: "resonance", hp: 1 },
  { x: 370, y: 565, kind: "resonance", hp: 1 },
  { x: 425, y: 650, kind: "resonance", hp: 1 },
  { x: 480, y: 735, kind: "resonance", hp: 1 },
  { x: 535, y: 820, kind: "resonance", hp: 1 },
  { x: 590, y: 905, kind: "resonance", hp: 1 },
  { x: 645, y: 990, kind: "resonance", hp: 1 },
  { x: 250, y: 440, kind: "crystal", hp: 1 },
  { x: 305, y: 525, kind: "crystal", hp: 1 },
  { x: 360, y: 610, kind: "crystal", hp: 1 },
  { x: 415, y: 695, kind: "crystal", hp: 1 },
  { x: 470, y: 780, kind: "crystal", hp: 1 },
  { x: 525, y: 865, kind: "crystal", hp: 1 },
  { x: 580, y: 950, kind: "crystal", hp: 1 },
  { x: 635, y: 1035, kind: "crystal", hp: 1 },
  { x: 380, y: 440, kind: "crystal", hp: 1 },
  { x: 435, y: 525, kind: "crystal", hp: 1 },
  { x: 490, y: 610, kind: "crystal", hp: 1 },
  { x: 545, y: 695, kind: "crystal", hp: 1 },
  { x: 600, y: 780, kind: "crystal", hp: 1 },
  { x: 655, y: 865, kind: "crystal", hp: 1 },
  ...row(400, 100, 240, 3, "crystal"),
  ...row(400, 480, 620, 3, "crystal"),
]

/** L9 晶簇堡垒：三层石梁分割的横向钉层（共鸣/晶体交替），侧翼冰柱。
 *  2026-09-28 实测：石梁 w=320 把左右通路封成 ~55px 窄缝，模拟过关率仅 6%（墙）。
 *  收窄到 w=240（两侧通道拓宽到 ~95px，球径 18 可过）后回到「有挑战非墙」。 */
const L9_OBSTACLES: ObstacleSpec[] = [
  { x: 360, y: 480, w: 240, h: 34, kind: "stone", hp: 2 },
  { x: 360, y: 720, w: 240, h: 34, kind: "stone", hp: 2 },
  { x: 360, y: 960, w: 240, h: 34, kind: "stone", hp: 2 },
  { x: 160, y: 700, w: 30, h: 120, kind: "ice", hp: 1 },
  { x: 560, y: 700, w: 30, h: 120, kind: "ice", hp: 1 },
]
const L9_PEGS: PegSpec[] = [
  ...row(400, 160, 560, 7, "crystal"),
  ...row(580, 160, 560, 7, "resonance"),
  ...row(660, 220, 500, 5, "resonance"),
  ...row(820, 160, 560, 7, "crystal"),
  ...row(900, 220, 500, 5, "crystal"),
  ...row(1060, 160, 560, 7, "resonance"),
  ...col(100, 480, 960, 7, "crystal"),
  ...col(620, 480, 960, 7, "crystal"),
]

/** L10 观星台终章：三大共鸣阵（高分压力）+ 四颗 hp=2 大钉 + 多障碍封锁。 */
const L10_OBSTACLES: ObstacleSpec[] = [
  { x: 360, y: 620, w: 260, h: 32, kind: "stone", hp: 2 },
  { x: 360, y: 840, w: 260, h: 32, kind: "stone", hp: 2 },
  { x: 120, y: 620, w: 28, h: 110, kind: "ice", hp: 1 },
  { x: 600, y: 620, w: 28, h: 110, kind: "ice", hp: 1 },
  { x: 120, y: 840, w: 28, h: 110, kind: "ice", hp: 1 },
  { x: 600, y: 840, w: 28, h: 110, kind: "ice", hp: 1 },
]
const L10_PEGS: PegSpec[] = [
  ...grid(180, 440, 6, 3, 72, 64, "resonance"),
  ...grid(180, 660, 6, 3, 72, 64, "resonance"),
  ...grid(180, 880, 6, 3, 72, 64, "resonance"),
  ...col(70, 440, 1008, 8, "crystal"),
  ...col(650, 440, 1008, 8, "crystal"),
  ...row(380, 220, 500, 5, "crystal"),
  ...row(1080, 220, 500, 5, "crystal"),
  // 四颗「大钉」（hp=2，重弹可一击碎）
  { x: 140, y: 400, kind: "crystal", hp: 2 },
  { x: 580, y: 400, kind: "crystal", hp: 2 },
  { x: 140, y: 1120, kind: "crystal", hp: 2 },
  { x: 580, y: 1120, kind: "crystal", hp: 2 },
]

export const LEVELS: LevelDef[] = [
  {
    id: 1,
    name: "星环序曲",
    targetScore: 800,
    balls: ["standard", "standard", "standard", "standard", "standard"],
    pegs: L1_PEGS,
    obstacles: [],
  },
  {
    id: 2,
    name: "共鸣回廊",
    targetScore: 1000,
    balls: ["standard", "standard", "standard", "standard", "standard"],
    pegs: L2_PEGS,
    obstacles: [],
  },
  {
    id: 3,
    name: "爆裂星簇",
    targetScore: 1400,
    balls: ["standard", "standard", "blast", "standard", "standard", "standard"],
    pegs: L3_PEGS,
    obstacles: [],
  },
  {
    id: 4,
    name: "石阵门关",
    targetScore: 1500,
    balls: ["standard", "heavy", "standard", "heavy", "standard", "standard"],
    pegs: L4_PEGS,
    obstacles: L4_OBSTACLES,
  },
  {
    id: 5,
    name: "穿晶长廊",
    targetScore: 2400,
    balls: ["standard", "standard", "pierce", "standard", "standard"],
    pegs: L5_PEGS,
    obstacles: [],
  },
  {
    id: 6,
    name: "冰环护盾",
    targetScore: 2600,
    balls: ["standard", "blast", "standard", "heavy", "pierce", "standard"],
    pegs: L6_PEGS,
    obstacles: L6_OBSTACLES,
  },
  {
    id: 7,
    name: "菱光矩阵",
    targetScore: 2800,
    balls: ["standard", "blast", "pierce", "heavy", "standard", "standard"],
    pegs: L7_PEGS,
    obstacles: L7_OBSTACLES,
  },
  {
    id: 8,
    name: "星瀑斜径",
    targetScore: 2700,
    balls: ["standard", "pierce", "standard", "blast", "heavy", "standard"],
    pegs: L8_PEGS,
    obstacles: L8_OBSTACLES,
  },
  {
    id: 9,
    name: "晶簇堡垒",
    targetScore: 3100,
    balls: ["heavy", "standard", "heavy", "pierce", "blast", "standard"],
    pegs: L9_PEGS,
    obstacles: L9_OBSTACLES,
  },
  {
    id: 10,
    name: "观星台终章",
    targetScore: 5100,
    balls: ["heavy", "blast", "standard", "pierce", "heavy", "standard"],
    pegs: L10_PEGS,
    obstacles: L10_OBSTACLES,
  },
]

/** 按 id 取关卡；不存在返回 undefined（调用方决定 no-op 或回退）。 */
export function getLevel(id: number): LevelDef | undefined {
  return LEVELS.find((l) => l.id === id)
}
