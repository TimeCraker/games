import { Container, Graphics, Sprite } from "pixi.js"

import type { ArenaDef, Obstacle } from "../content/arena"
import { radialGlow } from "./textures"
import { C } from "./art"

/**
 * 竞技场层：地面（细网格 + 中央光池）、硬边界、空间站舱段、管线。
 * 只在初始化时绘制一次 —— 运行时零成本。
 */
export function buildArena(arena: ArenaDef): Container {
  const root = new Container()
  const { halfW, halfH } = arena

  // 地面光池
  const pool = new Sprite(radialGlow("216,163,60", 256))
  pool.anchor.set(0.5)
  pool.position.set(0, 0)
  pool.width = halfW * 2.1
  pool.height = halfH * 2.1
  pool.alpha = 0.16
  pool.blendMode = "add"
  root.addChild(pool)

  const floor = new Graphics()
  // 可通行区底色（比虚空略亮，把「战场」从太空里读出来）
  floor.rect(-halfW, -halfH, halfW * 2, halfH * 2).fill({ color: 0x0d1218, alpha: 0.72 })
  // 细网格
  const step = 96
  for (let x = -halfW; x <= halfW; x += step) {
    floor.moveTo(x, -halfH).lineTo(x, halfH)
  }
  for (let y = -halfH; y <= halfH; y += step) {
    floor.moveTo(-halfW, y).lineTo(halfW, y)
  }
  floor.stroke({ width: 1, color: 0x8c949e, alpha: 0.10 })
  // 边界
  floor.roundRect(-halfW, -halfH, halfW * 2, halfH * 2, 48)
    .stroke({ width: 2, color: C.amber, alpha: 0.20 })
  // 四角括号（遥测台语言）
  const L = 74
  const corners: [number, number, number, number][] = [
    [-halfW, -halfH, 1, 1], [halfW, -halfH, -1, 1], [-halfW, halfH, 1, -1], [halfW, halfH, -1, -1],
  ]
  for (const [cx, cy, sx, sy] of corners) {
    floor.moveTo(cx + sx * L, cy).lineTo(cx, cy).lineTo(cx, cy + sy * L)
  }
  floor.stroke({ width: 5, color: C.amber, alpha: 0.5 })
  root.addChild(floor)

  // 管线（装饰，无碰撞）
  const pipes = new Graphics()
  for (const p of arena.pipes) {
    pipes.moveTo(p.x1, p.y1).lineTo(p.x2, p.y2)
    pipes.stroke({ width: p.w * 0.30 + 4, color: 0x05070a, alpha: 0.35 })
  }
  for (const p of arena.pipes) {
    pipes.moveTo(p.x1, p.y1).lineTo(p.x2, p.y2)
    pipes.stroke({ width: p.w * 0.30, color: 0x1d232a, alpha: 0.75 })
    pipes.moveTo(p.x1, p.y1).lineTo(p.x2, p.y2)
    pipes.stroke({ width: p.w * 0.10, color: 0x3a444e, alpha: 0.5 })
  }
  root.addChild(pipes)

  for (const o of arena.obstacles) root.addChild(buildObstacle(o))
  return root
}

/** 单个舱段：铸影 + 底板 + 受光顶边 + 面板缝 + 泛光条 + 细节件 */
function buildObstacle(o: Obstacle): Container {
  const g = new Graphics()
  const c = new Container()

  if (o.kind === "rect") {
    const { x, y, w, h } = o
    // 铸影
    g.roundRect(x + 14, y + 20, w, h, 8).fill({ color: 0x000000, alpha: 0.55 })
    // 底板
    g.roundRect(x, y, w, h, 8).fill({ color: 0x1b2128 }).stroke({ width: 2, color: C.ink })
    // 受光顶边
    g.moveTo(x + 6, y + 2).lineTo(x + w - 6, y + 2).stroke({ width: 2.4, color: C.amberMid, alpha: 0.30 })
    // 面板缝
    g.moveTo(x, y + h * 0.42).lineTo(x + w, y + h * 0.42).stroke({ width: 1.5, color: C.ink, alpha: 0.7 })
    g.moveTo(x + w * 0.5, y).lineTo(x + w * 0.5, y + h).stroke({ width: 1.5, color: C.ink, alpha: 0.55 })
    // 内嵌面板
    g.roundRect(x + w * 0.05, y + h * 0.12, w * 0.32, h * 0.2, 2)
      .fill({ color: 0x0e1319 }).stroke({ width: 1, color: 0x2e3339 })
    g.roundRect(x + w * 0.56, y + h * 0.16, w * 0.36, h * 0.12, 2)
      .fill({ color: 0x121820 }).stroke({ width: 1, color: 0x2e3339 })
    // 泛光条 + 灯
    g.roundRect(x + w * 0.07, y + h * 0.66, w * 0.22, 5, 2).fill({ color: C.amber, alpha: 0.85 })
    g.circle(x + w * 0.46, y + h * 0.70, 5).fill({ color: 0x0b0e12 }).stroke({ width: 1.2, color: 0x3a4249 })
    g.circle(x + w * 0.46, y + h * 0.70, 1.8).fill({ color: C.amberMid })
    g.circle(x + w * 0.54, y + h * 0.70, 5).fill({ color: 0x0b0e12 }).stroke({ width: 1.2, color: 0x3a4249 })
    g.circle(x + w * 0.54, y + h * 0.70, 1.8).fill({ color: C.amberMid, alpha: 0.5 })
  } else {
    const { x, y, r } = o
    g.circle(x + 13, y + 18, r).fill({ color: 0x000000, alpha: 0.55 })
    g.circle(x, y, r).fill({ color: 0x1b2128 }).stroke({ width: 2, color: C.ink })
    g.circle(x, y, r * 0.78).stroke({ width: 1.4, color: C.ink, alpha: 0.6 })
    g.circle(x, y, r * 0.48).fill({ color: 0x0e1319 }).stroke({ width: 1.2, color: 0x2e3339 })
    g.arc(x, y, r - 3, Math.PI * 1.05, Math.PI * 1.65).stroke({ width: 3, color: C.amberMid, alpha: 0.32 })
    g.circle(x, y, 6).fill({ color: C.amberMid })
    g.circle(x, y, 16).fill({ color: C.amber, alpha: 0.12 })
  }
  c.addChild(g)
  return c
}
