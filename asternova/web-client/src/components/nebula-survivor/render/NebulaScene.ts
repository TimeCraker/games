import { BlurFilter, Container, Graphics } from "pixi.js"

import { NebulaEngine, type EnemyTier, type NebulaEvent } from "../nebulaEngine"
import { NEBULA as C, TONES, TAU } from "./palette"
import { DamageNumbers } from "./DamageNumbers"

/** 屏震冲击波（击杀/升级/受击等事件驱动的径向环） */
interface Shockwave {
  x: number
  y: number
  t: number
  duration: number
  fromR: number
  toR: number
  color: number
  width: number
}

// ============ 静态矢量美术（庞家，均以 (0,0) 为中心、朝 +X 方向） ============

/** 主角飞船：赛璐璐三色调（平涂 base + 翼下暗面 + 脊线高光 + 深描边），机头朝 +X */
function paintPlayerShip(g: Graphics, r: number): void {
  const t = TONES.player
  const hull = [
    r * 1.16, 0,
    r * 0.12, r * 0.5,
    -r * 0.06, r * 1.06,
    -r * 0.42, r * 0.44,
    -r * 0.52, r * 0.28,
    -r * 1.08, 0,
    -r * 0.52, -r * 0.28,
    -r * 0.42, -r * 0.44,
    -r * 0.06, -r * 1.06,
    r * 0.12, -r * 0.5,
  ]
  g.poly(hull).fill({ color: t.base, alpha: 1 })
  g.poly(hull).stroke({ color: t.outline, width: 1.4, alpha: 1 })
  // 右翼暗面
  g.poly([r * 0.12, r * 0.5, -r * 0.06, r * 1.06, -r * 0.42, r * 0.44]).fill({ color: t.shadow, alpha: 0.85 })
  // 脊线高光
  g.moveTo(r * 0.9, 0).lineTo(-r * 0.5, 0).stroke({ color: t.hi, width: r * 0.16, alpha: 0.55 })
  // 驾驶舱圆顶 + 反光点
  g.circle(r * 0.34, 0, r * 0.32).fill({ color: t.hi, alpha: 1 }).stroke({ color: t.outline, width: 1, alpha: 0.9 })
  g.circle(r * 0.4, -r * 0.08, r * 0.12).fill({ color: 0xffffff, alpha: 0.95 })
}

/** 一档「探测箭镞」：锐三角赛璐璐 + 眼核（暖色外圈描边提示保留在 FX 层） */
function paintEnemyT1(g: Graphics, r: number): void {
  const t = TONES.enemy1
  const L = r * 1.9
  const W = r * 1.05
  g.poly([L, 0, -L * 0.55, -W, -L * 0.55, W]).fill({ color: t.base, alpha: 0.98 })
  g.poly([L, 0, -L * 0.55, -W, -L * 0.55, W]).stroke({ color: t.outline, width: 1.3, alpha: 0.95 })
  // 下三角暗面
  g.poly([L, 0, 0, W * 0.4, -L * 0.55, W]).fill({ color: t.shadow, alpha: 0.8 })
  // 前缘高光
  g.moveTo(L, 0).lineTo(0, -W * 0.2).stroke({ color: t.hi, width: W * 0.3, alpha: 0.5 })
  // 眼核
  g.circle(0, 0, r * 0.34).fill({ color: 0xfff3e6, alpha: 0.95 }).stroke({ color: t.outline, width: 0.8, alpha: 0.9 })
}

/** 二档「虚空碟」：六边形赛璐璐 + 内暗面六边形 + 高光环 + 核心 */
function paintEnemyT2(g: Graphics, r: number): void {
  const t = TONES.enemy2
  const R = r * 1.18
  const hex = (rad: number) => {
    const p: number[] = []
    for (let i = 0; i < 6; i++) {
      const a = Math.PI / 6 + (i / 6) * TAU
      p.push(Math.cos(a) * rad, Math.sin(a) * rad)
    }
    return p
  }
  g.poly(hex(R)).fill({ color: t.base, alpha: 0.97 })
  g.poly(hex(R)).stroke({ color: t.outline, width: 1.4, alpha: 0.95 })
  g.poly(hex(R * 0.62)).fill({ color: t.shadow, alpha: 0.5 })
  g.circle(0, 0, R * 0.5).stroke({ color: t.hi, width: 1.1, alpha: 0.7 })
  g.circle(0, 0, R * 0.22).fill({ color: 0xffffff, alpha: 0.95 })
}

/** 三档「巨舰」：四臂尖刺星赛璐璐 + 内暗面星 + 核心 */
function paintEnemyT3(g: Graphics, r: number): void {
  const t = TONES.enemy3
  const arms = 4
  const star = (outer: number, inner: number) => {
    const p: number[] = []
    for (let i = 0; i < arms * 2; i++) {
      const a = (i / (arms * 2)) * TAU - Math.PI / 2
      p.push(Math.cos(a) * (i % 2 === 0 ? outer : inner), Math.sin(a) * (i % 2 === 0 ? outer : inner))
    }
    return p
  }
  g.poly(star(r * 1.55, r * 0.6)).fill({ color: t.base, alpha: 0.98 })
  g.poly(star(r * 1.55, r * 0.6)).stroke({ color: t.outline, width: 1.6, alpha: 0.95 })
  g.poly(star(r * 0.95, r * 0.42)).fill({ color: t.shadow, alpha: 0.5 })
  g.circle(0, 0, r * 0.34).fill({ color: 0xffffff, alpha: 0.95 }).stroke({ color: t.outline, width: 1, alpha: 0.9 })
}

/** 激光弹：白热泪滴 + 琥珀描边 + 内核（机头朝 +X） */
function paintBullet(g: Graphics, r: number): void {
  const t = TONES.bullet
  const L = r * 2.3
  g.poly([L, 0, -L * 0.4, r * 0.6, -L * 0.8, 0, -L * 0.4, -r * 0.6]).fill({ color: t.base, alpha: 0.98 })
  g.poly([L, 0, -L * 0.4, r * 0.6, -L * 0.8, 0, -L * 0.4, -r * 0.6]).stroke({ color: t.outline, width: 0.7, alpha: 0.7 })
  g.circle(0, 0, r * 0.34).fill({ color: 0xffffff, alpha: 1 })
}

/** XP 结晶：菱形赛璐璐 + 右下暗面 + 高光切面 */
function paintCrystal(g: Graphics, r: number): void {
  const t = TONES.crystal
  const pts = [0, -r * 1.25, r * 0.85, 0, 0, r * 1.25, -r * 0.85, 0]
  g.poly(pts).fill({ color: t.base, alpha: 0.96 })
  g.poly(pts).stroke({ color: t.outline, width: 0.9, alpha: 0.92 })
  g.poly([0, 0, r * 0.85, 0, 0, r * 1.25]).fill({ color: t.shadow, alpha: 0.7 })
  g.poly([0, -r * 1.25, r * 0.3, -r * 0.4, -r * 0.3, -r * 0.4]).fill({ color: t.hi, alpha: 0.55 })
}

/** 急救包：品牌绿胶囊赛璐璐 + 白十字（暗面/高光） */
function paintHealth(g: Graphics, r: number): void {
  const t = TONES.heal
  g.circle(0, 0, r).fill({ color: t.base, alpha: 0.9 })
  g.circle(0, 0, r).stroke({ color: t.outline, width: 1.2, alpha: 0.92 })
  g.circle(0, r * 0.35, r * 0.72).fill({ color: t.shadow, alpha: 0.4 })
  g.circle(-r * 0.3, -r * 0.35, r * 0.3).fill({ color: t.hi, alpha: 0.5 })
  const cr = r * 0.56
  g.moveTo(-cr, 0).lineTo(cr, 0).moveTo(0, -cr).lineTo(0, cr).stroke({ color: 0xffffff, width: 1.8, alpha: 0.95 })
}

/** 星环粒子：冰白核心 + 高光点 */
function paintOrb(g: Graphics, r: number): void {
  const t = TONES.orb
  g.circle(0, 0, r * 1.15).fill({ color: t.base, alpha: 0.98 })
  g.circle(0, 0, r * 1.15).stroke({ color: t.outline, width: 0.8, alpha: 0.7 })
  g.circle(-r * 0.3, -r * 0.3, r * 0.4).fill({ color: 0xffffff, alpha: 0.9 })
}

// ============ 场景渲染层 ============

/**
 * 战斗场景渲染（Stage 视觉向升级：程序化矢量美术 + additive 柔光）。
 * 只读引擎状态做绘制，不改变任何模拟数值（玩法平衡不变）。
 * 分层：camera{ grid(normal) → world(normal 矢量体) → fx(add 柔光/粒子/冲击波) } + screenFx(add 全屏闪）。
 */
export class NebulaScene {
  readonly stage = new Container()
  private camera = new Container()

  private grid = new Graphics()
  private world = new Container()
  private glow = new Graphics()
  private fx = new Graphics()
  private screenFx = new Graphics()
  private damageNumbers = new DamageNumbers()
  private bloomFilters = [new BlurFilter({ strength: 4, quality: 2, kernelSize: 7 })]
  private bloomOn = true

  viewW = 800
  viewH = 600
  /** 命中减速（hit-stop）剩余秒：三档巨舰击杀冻结模拟约 45ms，仍持续渲染 */
  hitStop = 0

  private enemySprites = new Map<number, Graphics>()
  private bulletSprites = new Map<number, Graphics>()
  private crystalSprites = new Map<number, Graphics>()
  private healthSprites = new Map<number, Graphics>()
  private orbSprites: Graphics[] = []

  private playerSprite: Graphics
  private shockwaves: Shockwave[] = []
  private levelUpFlash = 0
  private playerAngle = -Math.PI / 2

  constructor(private readonly engine: NebulaEngine) {
    this.stage.addChild(this.camera)
    this.stage.addChild(this.screenFx)

    this.grid = new Graphics()
    this.world = new Container()
    this.glow = new Graphics()
    this.fx = new Graphics()
    this.glow.blendMode = "add"
    this.fx.blendMode = "add"
    this.screenFx.blendMode = "add"
    this.glow.filters = this.bloomFilters

    this.camera.addChild(this.grid)
    this.camera.addChild(this.world)
    this.camera.addChild(this.glow)
    this.camera.addChild(this.fx)
    this.camera.addChild(this.damageNumbers.container)

    this.playerSprite = new Graphics()
    paintPlayerShip(this.playerSprite, this.engine.player.r)
    this.world.addChild(this.playerSprite)

    for (let i = 0; i < 12; i++) {
      const o = new Graphics()
      paintOrb(o, 3.4)
      o.visible = false
      this.world.addChild(o)
      this.orbSprites.push(o)
    }

  }

  handleEvent(e: NebulaEvent): void {
    if (e.type === "damage") {
      this.damageNumbers.spawn(e.x, e.y, e.amount, this.engine.gameTime)
      return
    }
    if (e.type === "enemy-killed") {
      const color = e.tier === 1 ? C.enemy1 : e.tier === 2 ? C.enemy2 : C.enemy3
      this.pushShockwave(e.x, e.y, e.tier >= 2 ? 20 : 14, e.tier >= 2 ? 46 : 32, color)
      if (e.tier === 3) {
        this.pushShockwave(e.x, e.y, 12, 68, 0xffffff)
        this.hitStop = Math.max(this.hitStop, 0.045)
      }
    } else if (e.type === "level-up") {
      this.levelUpFlash = 1
      this.pushShockwave(this.engine.player.x, this.engine.player.y, 20, 96, C.azurite)
    } else if (e.type === "player-healed") {
      this.pushShockwave(e.x, e.y, 14, 42, C.heal)
    } else if (e.type === "player-died") {
      this.levelUpFlash = 0
      this.pushShockwave(this.engine.player.x, this.engine.player.y, 24, 180, 0xff4b4b)
      this.pushShockwave(this.engine.player.x, this.engine.player.y, 10, 120, 0xffffff)
    }
  }

  private pushShockwave(x: number, y: number, fromR: number, toR: number, color: number): void {
    if (this.shockwaves.length > 24) this.shockwaves.shift()
    this.shockwaves.push({ x, y, t: 0, duration: 0.4, fromR, toR, color, width: color === 0xffffff ? 2 : 3 })
  }

  /** 每帧由 Pixi ticker 调用（engine.update 已先行）。dtSec 为秒。 */
  sync(dtSec: number): void {
    const g = this.engine

    // 屏震（读引擎 hitShake）+ 相机对齐主角
    let sx = 0
    let sy = 0
    if (g.hitShake > 0) {
      const k = g.hitShake / 0.12
      sx = (Math.random() - 0.5) * 6 * k
      sy = (Math.random() - 0.5) * 6 * k
    }
    this.camera.position.set(this.viewW / 2 - g.player.x + sx, this.viewH / 2 - g.player.y + sy)

    // bloom 性能护栏：同屏敌人过载时回退为无滤波 additive 柔光
    const highLoad = g.em.enemies.length > 420
    if (highLoad !== this.bloomOn) {
      this.bloomOn = highLoad
      this.glow.filters = highLoad ? [] : this.bloomFilters
    }

    this.syncGrid()
    this.syncEnemies()
    this.syncBullets()
    this.syncPickups()
    this.syncOrbs()
    this.syncPlayer(dtSec)
    this.syncGlow()
    this.syncFx(dtSec)
  }

  private syncGrid(): void {
    const g = this.engine
    const px = g.player.x
    const py = g.player.y
    const hw = this.viewW / 2
    const hh = this.viewH / 2
    const grid = 64
    const gr = this.grid
    gr.clear()
    const x0 = Math.floor((px - hw) / grid) * grid
    const y0 = Math.floor((py - hh) / grid) * grid
    const x1 = px + hw
    const y1 = py + hh
    for (let x = x0; x <= x1; x += grid) {
      gr.moveTo(x, py - hh).lineTo(x, py + hh).stroke({ color: 0x8c949e, width: 1, alpha: 0.06 })
    }
    for (let y = y0; y <= y1; y += grid) {
      gr.moveTo(px - hw, y).lineTo(px + hw, y).stroke({ color: 0x8c949e, width: 1, alpha: 0.06 })
    }
  }

  private syncEnemies(): void {
    const g = this.engine
    const live = new Set<number>()
    const px = g.player.x
    const py = g.player.y
    for (const e of g.em.enemies) {
      if (!e.alive) continue
      live.add(e.id)
      let sprite = this.enemySprites.get(e.id)
      if (!sprite) {
        sprite = new Graphics()
        if (e.tier === 1) paintEnemyT1(sprite, e.r)
        else if (e.tier === 2) paintEnemyT2(sprite, e.r)
        else paintEnemyT3(sprite, e.r)
        this.world.addChild(sprite)
        this.enemySprites.set(e.id, sprite)
      }
      sprite.position.set(e.x, e.y)
      sprite.rotation = Math.atan2(py - e.y, px - e.x)
      sprite.visible = true
    }
    for (const [id, sp] of this.enemySprites) {
      if (!live.has(id)) {
        sp.destroy()
        this.enemySprites.delete(id)
      }
    }
  }

  private syncBullets(): void {
    const g = this.engine
    const live = new Set<number>()
    for (const b of g.bullets) {
      if (!b.alive) continue
      live.add(b.id)
      let sprite = this.bulletSprites.get(b.id)
      if (!sprite) {
        sprite = new Graphics()
        paintBullet(sprite, b.r)
        this.world.addChild(sprite)
        this.bulletSprites.set(b.id, sprite)
      }
      sprite.position.set(b.x, b.y)
      sprite.rotation = Math.atan2(b.vy, b.vx)
    }
    for (const [id, sp] of this.bulletSprites) {
      if (!live.has(id)) {
        sp.destroy()
        this.bulletSprites.delete(id)
      }
    }
  }

  private syncPickups(): void {
    const g = this.engine
    const tw = g.gameTime

    const cLive = new Set<number>()
    for (const c of g.crystals) {
      if (!c.alive) continue
      cLive.add(c.id)
      let sprite = this.crystalSprites.get(c.id)
      if (!sprite) {
        sprite = new Graphics()
        paintCrystal(sprite, c.r)
        this.world.addChild(sprite)
        this.crystalSprites.set(c.id, sprite)
      }
      sprite.position.set(c.x, c.y + Math.sin(tw * 3 + c.id * 0.7) * 2)
      sprite.scale.set(0.9 + 0.1 * Math.sin(tw * 4 + c.id))
    }
    for (const [id, sp] of this.crystalSprites) {
      if (!cLive.has(id)) {
        sp.destroy()
        this.crystalSprites.delete(id)
      }
    }

    const hLive = new Set<number>()
    for (const h of g.healthPacks) {
      if (!h.alive) continue
      hLive.add(h.id)
      let sprite = this.healthSprites.get(h.id)
      if (!sprite) {
        sprite = new Graphics()
        paintHealth(sprite, h.r)
        this.world.addChild(sprite)
        this.healthSprites.set(h.id, sprite)
      }
      sprite.position.set(h.x, h.y + Math.sin(tw * 2.4 + h.id) * 2)
    }
    for (const [id, sp] of this.healthSprites) {
      if (!hLive.has(id)) {
        sp.destroy()
        this.healthSprites.delete(id)
      }
    }
  }

  private syncOrbs(): void {
    const g = this.engine
    const orbs = g.getRingOrbPositions()
    for (let i = 0; i < this.orbSprites.length; i++) {
      const sp = this.orbSprites[i]
      const o = orbs[i]
      if (o) {
        sp.visible = true
        sp.position.set(o.ox, o.oy)
      } else {
        sp.visible = false
      }
    }
  }

  private syncPlayer(dtSec: number): void {
    const g = this.engine
    const px = g.player.x
    const py = g.player.y
    const mx = g.moveX
    const my = g.moveY
    const moving = Math.hypot(mx, my) > 0.12

    if (moving && !g.pausedUpgrade && !g.gameOver) {
      this.playerAngle = Math.atan2(my, mx)
    } else if (g.useMouseMove) {
      this.playerAngle = Math.atan2(g.mouseWorldY - py, g.mouseWorldX - px)
    }

    // 平滑转向（避免瞬间跳变）
    const target = this.playerAngle
    let da = target - this.playerSprite.rotation
    while (da > Math.PI) da -= TAU
    while (da < -Math.PI) da += TAU
    const turn = 14 * dtSec
    this.playerSprite.rotation = this.playerSprite.rotation + Math.max(-turn, Math.min(turn, da))

    this.playerSprite.position.set(px, py)
    this.playerSprite.visible = !g.gameOver

    // 无敌帧闪烁
    if (g.player.invuln > 0) {
      this.playerSprite.alpha = Math.sin(g.gameTime * 30) > 0 ? 0.35 : 0.9
    } else {
      this.playerSprite.alpha = 1
    }
  }

  /** 柔光层（additive + 高斯模糊 → 近似 bloom）：只画大面积软光斑，交给 blur 发亮光晕 */
  private syncGlow(): void {
    const g = this.engine
    const glow = this.glow
    glow.clear()

    const px = g.player.x
    const py = g.player.y

    for (const e of g.em.enemies) {
      if (!e.alive) continue
      const color = e.tier === 1 ? C.enemy1 : e.tier === 2 ? C.enemy2 : C.enemy3
      glow.circle(e.x, e.y, e.r * 2.6).fill({ color, alpha: 0.18 })
      glow.circle(e.x, e.y, e.r * 1.3).fill({ color, alpha: 0.13 })
    }

    for (const b of g.bullets) {
      if (!b.alive) continue
      const ang = Math.atan2(b.vy, b.vx)
      const tx = b.x - Math.cos(ang) * b.r * 2
      const ty = b.y - Math.sin(ang) * b.r * 2
      glow.circle(b.x, b.y, b.r * 2).fill({ color: C.laserMid, alpha: 0.55 })
      glow.circle(tx, ty, b.r * 2.8).fill({ color: C.laserOuter, alpha: 0.26 })
    }

    if (g.getRingOrbPositions().length > 0 && !g.pausedUpgrade && !g.gameOver) {
      for (const o of g.getRingOrbPositions()) {
        glow.circle(o.ox, o.oy, 10).fill({ color: C.orbFrost, alpha: 0.34 })
      }
    }

    for (const c of g.crystals) {
      if (!c.alive) continue
      glow.circle(c.x, c.y, c.r * 2.6).fill({ color: C.crystalOuter, alpha: 0.38 })
      glow.circle(c.x, c.y, c.r * 1.2).fill({ color: C.crystalMid, alpha: 0.44 })
    }
    for (const h of g.healthPacks) {
      if (!h.alive) continue
      glow.circle(h.x, h.y, h.r * 2.4).fill({ color: C.heal, alpha: 0.44 })
    }

    glow.circle(px, py, g.player.r * 2.1).fill({ color: C.azurite, alpha: 0.2 })
    if (Math.hypot(g.moveX, g.moveY) > 0.12 && !g.gameOver) {
      const ang = this.playerAngle
      const backX = px - Math.cos(ang) * g.player.r * 1.15
      const backY = py - Math.sin(ang) * g.player.r * 1.15
      glow.circle(backX, backY, 9).fill({ color: C.azurite, alpha: 0.6 })
      glow.circle(backX, backY, 15).fill({ color: C.laserMid, alpha: 0.2 })
    }
  }

  /** 锐利 FX 层（additive，无模糊）：描边环 / 粒子 / 尾迹 / 碎块 / 冲击波 / 全屏闪 + 飘字更新 */
  private syncFx(dtSec: number): void {
    const g = this.engine
    const fx = this.fx
    fx.clear()

    // 一档暖色外圈描边（玩法提示，脉冲呼吸）
    for (const e of g.em.enemies) {
      if (!e.alive || e.tier !== 1) continue
      const pulse = 0.5 + 0.5 * Math.sin(g.gameTime * 4.2 + e.id * 0.7)
      fx.circle(e.x, e.y, e.r + 6 + pulse * 2.5).stroke({ color: C.enemy1rim, width: 1.4, alpha: 0.4 + pulse * 0.3 })
    }

    for (const q of g.particles) {
      const a = Math.max(0, q.life / 0.55)
      let color = 0xe9be69
      if (q.kind === "gold") color = 0xd8a33c
      if (q.kind === "white") color = 0xfff6e2
      fx.circle(q.x, q.y, q.size * (0.5 + a * 0.5)).fill({ color, alpha: (0.4 + a * 0.5) * 0.9 })
    }

    for (const t of g.trails) {
      const a = 1 - t.life / t.maxLife
      const s = t.size * (0.4 + 0.6 * (1 - a))
      fx.circle(t.x, t.y, s).fill({ color: 0xf2d79b, alpha: 0.45 * (1 - a) })
    }

    for (const s of g.shards) {
      const a = 1 - s.life / s.maxLife
      let color = 0xd8a33c
      if (s.tier === 1) color = 0xc08069
      if (s.tier === 2) color = 0x7fb39e
      fx.circle(s.x, s.y, s.size).fill({ color, alpha: (0.2 + a * 0.8) })
    }

    for (let i = this.shockwaves.length - 1; i >= 0; i--) {
      const sw = this.shockwaves[i]
      sw.t += dtSec
      const p = Math.min(1, sw.t / sw.duration)
      if (p >= 1) {
        this.shockwaves.splice(i, 1)
        continue
      }
      const rr = sw.fromR + (sw.toR - sw.fromR) * p
      fx.circle(sw.x, sw.y, rr).stroke({ color: sw.color, width: sw.width * (1 - p) + 0.5, alpha: (1 - p) * 0.9 })
    }

    this.damageNumbers.update(dtSec)

    // ---- 全屏闪焦（screenFx）----
    const sf = this.screenFx
    sf.clear()
    if (g.hitFlash > 0) {
      const hf = g.hitFlash / 0.14
      sf.rect(0, 0, this.viewW, this.viewH).fill({ color: 0xff2b4b, alpha: 0.12 * hf })
    }
    if (this.levelUpFlash > 0) {
      this.levelUpFlash = Math.max(0, this.levelUpFlash - dtSec * 2.2)
      sf.rect(0, 0, this.viewW, this.viewH).fill({ color: C.azurite, alpha: 0.16 * this.levelUpFlash })
      sf.rect(0, 0, this.viewW, this.viewH).fill({ color: 0xffffff, alpha: 0.08 * this.levelUpFlash })
    }
  }

  destroy(): void {
    this.stage.destroy({ children: true })
  }
}
