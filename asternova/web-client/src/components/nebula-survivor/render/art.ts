import { Graphics } from "pixi.js"

import type { EnemyKind, WeaponId } from "../sim/types"

/**
 * 矢量美术（赛璐璐三色调：base / shadow / hi + 深描边）
 * 全部为**俯视角**造型；这里画的是「以 (0,0) 为中心」的静态形状，
 * 由 NebulaScene 在启动时烘焙成 texture，运行时用 Sprite 复用（可 tint、可旋转）。
 */
export const C = {
  ink: 0x05070a,
  hullDark: 0x171c22,
  hull: 0x2a3138,
  hullLit: 0x4a545e,
  amber: 0xd8a33c,
  amberHi: 0xfff6e2,
  amberMid: 0xe9be69,
  amberDim: 0x8a6519,
  moss: 0x9cb86a,
  steel: 0x8fb3c9,
  coral: 0xc08069,
  coralRim: 0xe8cbb8,
  teal: 0x7fb39e,
  tealRim: 0xcfe8de,
  red: 0xc0503a,
  redRim: 0xe0a99b,
} as const

function fillStroke(g: Graphics, fill: number, alpha: number, strokeW = 0, stroke = C.ink, strokeAlpha = 1) {
  g.fill({ color: fill, alpha })
  if (strokeW > 0) g.stroke({ width: strokeW, color: stroke, alpha: strokeAlpha })
}

/** 玩家舰：宽体船身 + 后掠翼 + 翼尖灯舱 + 双引擎喷口 + 舰首炮口（俯视，机首朝 -y） */
export function drawShip(g: Graphics): void {
  // 引擎焰
  g.ellipse(-8, 46, 7, 18).fill({ color: C.amberMid, alpha: 0.45 })
  g.ellipse(8, 46, 7, 18).fill({ color: C.amberMid, alpha: 0.45 })
  g.ellipse(-8, 40, 4.5, 12).fill({ color: C.amberHi, alpha: 0.9 })
  g.ellipse(8, 40, 4.5, 12).fill({ color: C.amberHi, alpha: 0.9 })
  // 后掠翼
  g.poly([-12, -3, -34, 12, -31, 26, -11, 17]).fill({ color: C.hullDark })
  g.poly([-12, -3, -34, 12, -31, 26, -11, 17]).stroke({ width: 2, color: C.ink })
  g.poly([12, -3, 34, 12, 31, 26, 11, 17]).fill({ color: C.hullDark })
  g.poly([12, -3, 34, 12, 31, 26, 11, 17]).stroke({ width: 2, color: C.ink })
  // 翼尖灯舱
  g.roundRect(-39, 7, 8, 15, 2).fill({ color: 0x22262b }).stroke({ width: 1.5, color: C.ink })
  g.roundRect(31, 7, 8, 15, 2).fill({ color: 0x22262b }).stroke({ width: 1.5, color: C.ink })
  g.circle(-35, 10, 1.9).fill({ color: C.amberMid })
  g.circle(35, 10, 1.9).fill({ color: C.amberMid, alpha: 0.75 })
  // 翼上武器硬点
  g.roundRect(-27, 3, 11, 4, 1).fill({ color: C.amber, alpha: 0.9 })
  g.roundRect(16, 3, 11, 4, 1).fill({ color: C.amber, alpha: 0.9 })
  // 船体（前尖后宽）
  g.moveTo(0, -33).bezierCurveTo(6, -24, 11, -14, 11, -2)
  g.lineTo(13, 26).lineTo(-13, 26).lineTo(-11, -2)
  g.bezierCurveTo(-11, -14, -6, -24, 0, -33).closePath()
  g.fill({ color: C.hull }).stroke({ width: 2.5, color: C.ink })
  // 赛璐璐二分（右背光 / 左受光）
  g.moveTo(0, -33).bezierCurveTo(6, -24, 11, -14, 11, -2)
  g.lineTo(13, 26).lineTo(0, 26).closePath().fill({ color: 0x0f1318, alpha: 0.72 })
  // 座舱
  g.moveTo(0, -25).bezierCurveTo(4.5, -20, 6, -12, 5, -4)
  g.lineTo(-5, -4).bezierCurveTo(-6, -12, -4.5, -20, 0, -25).closePath()
  g.fill({ color: C.amber }).stroke({ width: 1.2, color: C.amberDim })
  g.moveTo(0, -25).bezierCurveTo(3, -21, 4, -16, 4, -12).lineTo(0, -12).closePath().fill({ color: C.amberHi })
  // 引擎喷口
  g.roundRect(-12, 24, 9, 9, 2).fill({ color: 0x0b0e12 }).stroke({ width: 1.3, color: C.hullLit })
  g.roundRect(3, 24, 9, 9, 2).fill({ color: 0x0b0e12 }).stroke({ width: 1.3, color: C.hullLit })
  // 舰首炮口
  g.moveTo(0, -33).lineTo(0, -42).stroke({ width: 2.6, color: C.amberMid, cap: "round" })
}

/** 敌群：三档 + Boss，各自的剪影与 rim light 都不同，暗底可辨 */
export function drawEnemy(g: Graphics, kind: EnemyKind): void {
  const spec = {
    scout: { base: C.coral, rim: C.coralRim, edge: 0x3a1a10 },
    drone: { base: C.teal, rim: C.tealRim, edge: 0x1c3830 },
    heavy: { base: C.red, rim: C.redRim, edge: 0x40140c },
    boss: { base: C.red, rim: C.redRim, edge: 0x40140c },
  }[kind]

  if (kind === "scout") {
    // 尖头游猎机（朝 -y）
    g.moveTo(0, -16).lineTo(13, 6).lineTo(4, 2).lineTo(3, 13).lineTo(-3, 13).lineTo(-4, 2).lineTo(-13, 6).closePath()
    g.fill({ color: spec.base }).stroke({ width: 2, color: spec.edge })
    g.moveTo(0, -16).lineTo(13, 6).lineTo(4, 2).closePath().fill({ color: spec.rim, alpha: 0.55 })
    g.circle(0, -4, 3).fill({ color: spec.rim, alpha: 0.9 })
  } else if (kind === "drone") {
    // 六边形蜂群机
    g.poly([0, -17, 15, -8, 15, 8, 0, 17, -15, 8, -15, -8]).closePath()
    g.fill({ color: spec.base }).stroke({ width: 2, color: spec.edge })
    g.poly([0, -17, 15, -8, 0, -4, -15, -8]).closePath().fill({ color: spec.rim, alpha: 0.45 })
    g.roundRect(-7, -3, 14, 5, 2).fill({ color: 0x0b0e12, alpha: 0.8 })
  } else if (kind === "heavy") {
    // 重甲机：方形装甲 + 撞角
    g.roundRect(-16, -16, 32, 32, 4).fill({ color: spec.base }).stroke({ width: 2.4, color: spec.edge })
    g.roundRect(-16, -16, 32, 10, 3).fill({ color: spec.rim, alpha: 0.4 })
    g.moveTo(0, -16).lineTo(0, -26).stroke({ width: 3, color: spec.rim, alpha: 0.8, cap: "round" })
    g.roundRect(-11, -2, 8, 8, 2).fill({ color: 0x0b0e12, alpha: 0.85 })
    g.roundRect(3, -2, 8, 8, 2).fill({ color: 0x0b0e12, alpha: 0.85 })
  } else {
    // Boss：多层核心 + 外环
    g.circle(0, 0, 46).fill({ color: 0x1a0d09 }).stroke({ width: 3, color: spec.edge })
    g.circle(0, 0, 46).stroke({ width: 1.5, color: spec.rim, alpha: 0.35 })
    g.poly([0, -34, 22, -14, 22, 14, 0, 34, -22, 14, -22, -14]).closePath()
      .fill({ color: spec.base }).stroke({ width: 2.5, color: spec.edge })
    g.circle(0, 0, 16).fill({ color: spec.rim, alpha: 0.95 })
    g.circle(0, 0, 26).stroke({ width: 2, color: spec.rim, alpha: 0.5 })
  }
}

/** 玩家弹（琥珀能量弹） */
export function drawBullet(g: Graphics): void {
  g.circle(0, 0, 7).fill({ color: C.amber, alpha: 0.22 })
  g.circle(0, 0, 4).fill({ color: C.amberMid, alpha: 0.9 })
  g.circle(0, 0, 2).fill({ color: C.amberHi })
}
/** 敌方弹（信号红） */
export function drawEnemyShot(g: Graphics): void {
  g.circle(0, 0, 9).fill({ color: C.red, alpha: 0.20 })
  g.circle(0, 0, 4.5).fill({ color: C.red })
  g.circle(0, 0, 2).fill({ color: C.redRim })
}

/** 掉落物 */
export function drawDrop(g: Graphics, kind: "coin" | "xp" | "health" | "weapon", tierColor = C.amber): void {
  if (kind === "coin") {
    g.circle(0, 0, 9).fill({ color: C.amber, alpha: 0.18 })
    g.circle(0, 0, 5).fill({ color: C.amber }).stroke({ width: 1.2, color: C.amberDim })
    g.circle(0, -1.4, 1.8).fill({ color: C.amberHi, alpha: 0.9 })
  } else if (kind === "xp") {
    g.circle(0, 0, 12).fill({ color: C.amberHi, alpha: 0.14 })
    g.poly([0, -7, 5, 0, 0, 7, -5, 0]).closePath().fill({ color: C.amber }).stroke({ width: 1.2, color: C.amberDim })
    g.poly([0, -7, 5, 0, 0, 2]).closePath().fill({ color: C.amberHi, alpha: 0.9 })
  } else if (kind === "health") {
    g.circle(0, 0, 11).fill({ color: C.moss, alpha: 0.16 })
    g.roundRect(-7, -7, 14, 14, 3).fill({ color: 0x4f8d6b }).stroke({ width: 1.5, color: 0xcfe8de })
    g.rect(-1.6, -4.5, 3.2, 9).fill({ color: 0xcfe8de })
    g.rect(-4.5, -1.6, 9, 3.2).fill({ color: 0xcfe8de })
  } else {
    // 武器补给：品级色菱形 + 竖起的武器示意
    g.circle(0, 0, 15).fill({ color: tierColor, alpha: 0.18 })
    g.poly([0, -12, 12, 0, 0, 12, -12, 0]).closePath().fill({ color: tierColor }).stroke({ width: 1.6, color: C.ink })
    g.rect(-1.6, -7, 3.2, 14).fill({ color: 0x0b0e12, alpha: 0.85 })
  }
}

/** 法术场：三种场用不同环语言区分（白皮书 §5.1「在地上放一个场」） */
export function drawField(g: Graphics, weapon: WeaponId, r: number): void {
  if (weapon === "well") {
    g.circle(0, 0, r).fill({ color: C.amber, alpha: 0.07 })
    g.circle(0, 0, r).stroke({ width: 2, color: C.amber, alpha: 0.45 })
    g.circle(0, 0, r * 0.62).stroke({ width: 1.4, color: C.amberMid, alpha: 0.5 })
    g.circle(0, 0, r * 0.28).stroke({ width: 1.2, color: C.amberHi, alpha: 0.6 })
    for (let i = 0; i < 3; i++) {
      const a = (i / 3) * Math.PI * 2
      g.moveTo(Math.cos(a) * r * 0.3, Math.sin(a) * r * 0.3)
      g.lineTo(Math.cos(a) * r * 0.92, Math.sin(a) * r * 0.92)
        .stroke({ width: 1.2, color: C.amberMid, alpha: 0.35 })
    }
  } else if (weapon === "repulse") {
    g.circle(0, 0, r).stroke({ width: 3, color: C.amber, alpha: 0.55 })
    g.circle(0, 0, r * 0.82).stroke({ width: 1.5, color: C.amberHi, alpha: 0.35 })
  } else {
    // 空间裂缝：撕裂的锯齿环
    g.circle(0, 0, r).fill({ color: 0x2a1030, alpha: 0.22 })
    g.circle(0, 0, r).stroke({ width: 2, color: C.steel, alpha: 0.5 })
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2
      const a2 = a + 0.22
      g.moveTo(Math.cos(a) * r * 0.5, Math.sin(a) * r * 0.5)
      g.lineTo(Math.cos(a2) * r * 1.05, Math.sin(a2) * r * 1.05)
        .stroke({ width: 1.4, color: C.steel, alpha: 0.55 })
    }
  }
}

/** 品级色（白皮书 §5.2：直接映射既有品牌 token） */
export const TIER_COLORS = [C.amberHi, C.moss, C.steel, C.amber, C.red] as const
export function tierColor(stars: number): number {
  return TIER_COLORS[Math.max(0, Math.min(TIER_COLORS.length - 1, stars - 1))]
}
