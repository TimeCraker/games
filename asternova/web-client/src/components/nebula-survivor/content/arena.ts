/**
 * 竞技场（白皮书 §8）：有限边界 + 墙 / 掩体 / 通道。
 *
 * 主题：废弃矿星 · 7 号采掘平台。
 * 世界坐标原点在竞技场中心；相机以玩家为中心，竞技场有硬边界。
 *
 * 坐标系与数值一律为「世界单位」，渲染层按相机缩放绘制，不含任何像素假设。
 */
export type Obstacle =
  | { kind: "rect"; x: number; y: number; w: number; h: number }
  | { kind: "circle"; x: number; y: number; r: number }

export type ArenaDef = {
  id: string
  name: string
  /** 可通行区边界（中心在原点的矩形） */
  halfW: number
  halfH: number
  obstacles: Obstacle[]
  /** 纯装饰管线（无碰撞），渲染层用 */
  pipes: { x1: number; y1: number; x2: number; y2: number; w: number }[]
  /** 起始安全区半径（出生点周围不刷怪） */
  safeR: number
}

export const ARENA_MINE_7: ArenaDef = {
  id: "mine-7",
  name: "废弃矿星 · 7 号采掘平台",
  halfW: 1180,
  halfH: 820,
  obstacles: [
    // 左上大型舱段
    { kind: "rect", x: -1048, y: -636, w: 460, h: 236 },
    // 右侧纵向舱段
    { kind: "rect", x: 768, y: -476, w: 300, h: 472 },
    // 底部横向长舱
    { kind: "rect", x: -504, y: 504, w: 536, h: 160 },
    // 圆形储罐
    { kind: "circle", x: -684, y: 132, r: 108 },
    // 新增：两处小掩体，制造通道感
    { kind: "rect", x: 180, y: 300, w: 190, h: 110 },
    { kind: "circle", x: 560, y: 560, r: 84 },
  ],
  pipes: [
    { x1: -600, y1: 660, x2: 20, y2: -60, w: 16 },
    { x1: -600, y1: 660, x2: 780, y2: -20, w: 12 },
  ],
  safeR: 260,
}

export const ARENAS = { [ARENA_MINE_7.id]: ARENA_MINE_7 }
export const DEFAULT_ARENA = ARENA_MINE_7
