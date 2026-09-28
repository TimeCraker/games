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

/**
 * 玩家单位：**舰装少女**（俯视）。
 *
 * 设定（2026-09-27 制作人拍板）：玩家不是匿名战舰，而是「人形本体 + 舰装挂架」——
 * 本体是人形角色，两侧是可换装 / 可收集的舰装挂架。俯视可读性靠三件事：
 *   ① 头（珍珠白发 + 冷蓝阴影） ② 左右对称的舰装挂架 ③ 下方推进焰
 * 配色沿用品牌：象牙白 / 冷蓝 / 琥珀；舰装本体冷钢灰。
 */
export function drawPilot(g: Graphics): void {
  const HAIR = 0xf0f2fa
  const HAIR_DEEP = 0x9aa6c8
  const SUIT = 0x1d232b
  const SUIT_LIT = 0x333c48
  const RIGGING = 0x232a32
  const RIGGING_LIT = 0x3d4650

  // ══ 俯视可读性原则 ══
  // 正俯视看人只剩「头顶 + 肩」，若两侧再横向展开装备就必然读成飞行器。
  // 因此：① 人形剪影占绝对主导 ② 靠**长发 + 钟形裙摆**给出径向可读的少女轮廓
  // ③ 舰装挂架收进肩侧、纵向摆放，绝不做成机翼。

  // ── 舰装推进焰（肩侧挂架后方，短促）──
  g.ellipse(-12, 17, 3.6, 11).fill({ color: C.amberMid, alpha: 0.38 })
  g.ellipse(12, 17, 3.6, 11).fill({ color: C.amberMid, alpha: 0.38 })
  g.ellipse(-12, 14, 2.2, 6).fill({ color: C.amberHi, alpha: 0.9 })
  g.ellipse(12, 14, 2.2, 6).fill({ color: C.amberHi, alpha: 0.9 })

  // ── 舰装挂架：肩侧纵向小型装备舱（换装/收集的载体，绝不横向展开）──
  for (const s of [-1, 1]) {
    const x = s * 12
    g.roundRect(x - 4.4, -13, 8.8, 17, 4).fill({ color: RIGGING }).stroke({ width: 1.5, color: C.ink })
    g.roundRect(x - 4.4, -13, 8.8, 5.5, 3).fill({ color: RIGGING_LIT, alpha: 0.9 })
    g.roundRect(x - 4.4, -6.5, 8.8, 2.4, 1).fill({ color: C.amber, alpha: 0.92 })
    g.roundRect(x - 2.8, 3, 5.6, 4, 1.4).fill({ color: 0x0b0e12 }).stroke({ width: 1, color: RIGGING_LIT })
    g.circle(x - s * 1.6, -1, 1.3).fill({ color: C.amberMid })
    // 与肩部的短连接架（贴合身体，不外张）
    g.moveTo(x - s * 4.4, -8).lineTo(s * 7, -9).stroke({ width: 2.6, color: C.hullDark })
  }

  // ── 长发（俯视第一可读特征：从头顶向外后方铺开的大形态）──
  g.moveTo(-9.5, -15)
  g.bezierCurveTo(-17, -4, -18.5, 9, -11, 19)
  g.lineTo(11, 19)
  g.bezierCurveTo(18.5, 9, 17, -4, 9.5, -15)
  g.closePath().fill({ color: HAIR_DEEP, alpha: 0.85 })
  g.moveTo(-6.5, -14)
  g.bezierCurveTo(-12, -4, -13, 8, -8, 17)
  g.lineTo(8, 17)
  g.bezierCurveTo(13, 8, 12, -4, 6.5, -14)
  g.closePath().fill({ color: HAIR, alpha: 0.55 })

  // ── 钟形裙摆（俯视读作圆，任何旋转角度都成立）──
  g.moveTo(-9, -1)
  g.bezierCurveTo(-14.5, 4, -16.5, 11, -16, 17)
  g.lineTo(16, 17)
  g.bezierCurveTo(16.5, 11, 14.5, 4, 9, -1)
  g.closePath().fill({ color: SUIT }).stroke({ width: 2, color: C.ink })
  // 裙摆受光面
  g.moveTo(-9, -1).bezierCurveTo(-14.5, 4, -16.5, 11, -16, 17).lineTo(-3, 17).lineTo(-3, -1).closePath()
  g.fill({ color: SUIT_LIT, alpha: 0.45 })
  // 裙摆琥珀滚边
  g.moveTo(-16, 16.6).lineTo(16, 16.6).stroke({ width: 1.6, color: C.amberDim, alpha: 0.8 })

  // ── 手臂（贴身，不横向伸展）──
  g.roundRect(-11.4, -12, 4.4, 14, 2).fill({ color: SUIT }).stroke({ width: 1.2, color: C.ink })
  g.roundRect(7, -12, 4.4, 14, 2).fill({ color: SUIT }).stroke({ width: 1.2, color: C.ink })

  // ── 躯干（束腰，肩窄腰细）──
  g.moveTo(-7, -14)
  g.bezierCurveTo(-8.6, -8, -6.4, -2, -5.4, 1)
  g.lineTo(5.4, 1)
  g.bezierCurveTo(6.4, -2, 8.6, -8, 7, -14)
  g.closePath().fill({ color: SUIT }).stroke({ width: 1.8, color: C.ink })
  g.moveTo(-7, -14).bezierCurveTo(-8.6, -8, -6.4, -2, -5.4, 1).lineTo(-5, -14).closePath()
  g.fill({ color: SUIT_LIT, alpha: 0.75 })
  // 胸前琥珀电源核心
  g.circle(0, -7, 2.2).fill({ color: C.amber })
  g.circle(0, -7, 4.2).stroke({ width: 1, color: C.amber, alpha: 0.4 })

  // ── 肩甲（小巧，不外扩）──
  g.roundRect(-10, -15.5, 6.4, 5.6, 2.6).fill({ color: RIGGING }).stroke({ width: 1.3, color: C.ink })
  g.roundRect(3.6, -15.5, 6.4, 5.6, 2.6).fill({ color: RIGGING }).stroke({ width: 1.3, color: C.ink })

  // ── 头（俯视看到的是发顶；大而明确）──
  g.circle(0, -21, 9).fill({ color: HAIR_DEEP }).stroke({ width: 1.6, color: C.ink })
  g.circle(-1, -22, 7.2).fill({ color: HAIR })
  g.moveTo(0, -30).lineTo(0, -14).stroke({ width: 1, color: HAIR_DEEP, alpha: 0.85 })
  // 前额琥珀传感片（俯视唯一能看见的「脸」）
  g.roundRect(-3.4, -27.5, 6.8, 3, 1.4).fill({ color: C.amber })
  g.roundRect(-3.4, -27.5, 3.2, 3, 1.4).fill({ color: C.amberHi })

  // ── 手持武器（右手前方，给出朝向读点）──
  g.moveTo(6, -24).lineTo(6, -37).stroke({ width: 2.6, color: C.amberMid, cap: "round" })
  g.circle(6, -37, 1.9).fill({ color: C.amberHi })
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
