import { Container, Graphics, Sprite, Text, Texture, type Renderer } from "pixi.js"

import type { Sim } from "../sim/Sim"
import type { EnemyKind, SimEvent, WeaponId } from "../sim/types"
import { buildArena } from "./arena"
import { C, drawBullet, drawDrop, drawEnemy, drawEnemyShot, drawField, drawPilot, tierColor } from "./art"
import { NebulaBackground } from "./bg"
import { whitePixel } from "./textures"

/** 一个可复用的精灵层：每帧 begin() → take() → end()，多余的一律隐藏 */
class Pool {
  private used = 0
  private items: Sprite[] = []
  constructor(private parent: Container) {}
  begin(): void { this.used = 0 }
  take(tex: Texture): Sprite {
    let s = this.items[this.used]
    if (!s) {
      s = new Sprite(tex)
      s.anchor.set(0.5)
      this.items.push(s)
      this.parent.addChild(s)
    }
    s.texture = tex
    s.visible = true
    s.alpha = 1
    s.tint = 0xffffff
    s.rotation = 0
    s.scale.set(1)
    s.blendMode = "normal"
    this.used++
    return s
  }
  end(): void {
    for (let i = this.used; i < this.items.length; i++) this.items[i].visible = false
  }
}

type Float = { t: Text; life: number; maxLife: number; x: number; y: number; vy: number }

export class NebulaScene {
  readonly stage = new Container()
  private camera = new Container()
  private bg = new NebulaBackground()
  private worldFx = new Container()
  private fieldLayer = new Pool(this.worldFx)
  private dropLayer = new Pool(this.worldFx)
  private enemyLayer = new Pool(this.worldFx)
  private bulletLayer = new Pool(this.worldFx)
  private shipLayer = new Pool(this.worldFx)
  private particleLayer = new Pool(this.worldFx)
  private floatLayer = new Container()

  private tex!: {
    ship: Texture
    enemy: Record<EnemyKind, Texture>
    bullet: Texture
    eshot: Texture
    coin: Texture
    xp: Texture
    health: Texture
    weapon: Record<string, Texture>
    field: Record<string, Texture>
    px: Texture
  }

  private floats: Float[] = []
  private shocks: { g: Graphics; life: number; maxLife: number; r: number; color: number }[] = []
  private flash = 0
  private hurtFlash = 0
  /** 命中顿感（秒）：由 host 读取，>0 时冻结模拟但仍推进渲染 */
  hitStop = 0
  private shakeT = 0
  private shakeMag = 0

  viewW = 800
  viewH = 600
  zoom = 1

  constructor(private readonly renderer: Renderer) {
    this.stage.addChild(this.bg.container)
    this.stage.addChild(this.camera)
  }

  /** 启动时把所有实体烘焙成 texture：运行时只移动 Sprite，不再重绘矢量 */
  init(sim: Sim): void {
    const bakeAt = (draw: (g: Graphics) => void) => {
      const g = new Graphics()
      draw(g)
      return this.renderer.generateTexture({ target: g, resolution: 2, antialias: true })
    }

    const enemyTex = {} as Record<EnemyKind, Texture>
    for (const k of ["scout", "drone", "heavy", "boss"] as EnemyKind[]) {
      enemyTex[k] = bakeAt((g) => drawEnemy(g, k))
    }
    const fieldTex = {} as Record<string, Texture>
    for (const w of ["well", "repulse", "rift"] as WeaponId[]) {
      fieldTex[w] = bakeAt((g) => drawField(g, w, 100))
    }
    const weaponTex: Record<string, Texture> = {}
    for (const id of sim.cls.weapons) {
      weaponTex[id] = bakeAt((g) => drawDrop(g, "weapon", C.amber))
    }

    this.tex = {
      ship: bakeAt(drawPilot),
      enemy: enemyTex,
      bullet: bakeAt(drawBullet),
      eshot: bakeAt(drawEnemyShot),
      coin: bakeAt((g) => drawDrop(g, "coin")),
      xp: bakeAt((g) => drawDrop(g, "xp")),
      health: bakeAt((g) => drawDrop(g, "health")),
      weapon: weaponTex,
      field: fieldTex,
      px: whitePixel(),
    }

    this.worldFx.addChild(buildArena(sim.arena))
    this.camera.addChild(this.worldFx)
    // 法术场在地面之上、实体之下
    this.worldFx.addChild(this.floatLayer)
  }

  setSize(w: number, h: number): void {
    this.viewW = w
    this.viewH = h
    this.bg.setSize(w, h)
    // 相机缩放：保证任何纵横比下都能看到足够战斗信息（白皮书 §11.7 的可见性口径）
    this.zoom = Math.max(0.80, Math.min(1.15, Math.min(w, h * 1.55) / 1080))
  }

  private addFloat(x: number, y: number, text: string, color: number, size = 15): void {
    if (this.floats.length > 90) return
    const t = new Text({
      text,
      style: { fontFamily: "ui-monospace, JetBrains Mono, Consolas, monospace", fontSize: size, fontWeight: "700", fill: color },
    })
    t.anchor.set(0.5)
    t.position.set(x, y)
    this.floatLayer.addChild(t)
    this.floats.push({ t, life: 0.75, maxLife: 0.75, x, y, vy: -34 })
  }

  private addShock(x: number, y: number, r: number, color: number): void {
    const g = new Graphics()
    g.position.set(x, y)
    this.worldFx.addChild(g)
    this.shocks.push({ g, life: 0.42, maxLife: 0.42, r, color })
  }

  handleEvent(e: SimEvent): void {
    switch (e.type) {
      case "hit":
        this.addFloat(e.x, e.y - 14, String(e.amount), C.amberHi, e.crit ? 19 : 14)
        break
      case "kill": {
        this.addShock(e.x, e.y, e.kind === "boss" ? 340 : 74, e.kind === "scout" ? C.coral : e.kind === "drone" ? C.teal : C.red)
        this.hitStop = e.kind === "boss" ? 0.20 : e.kind === "heavy" ? 0.075 : 0.035
        if (e.kind === "boss") this.flash = 0.55
        this.shake(e.kind === "boss" ? 16 : 4, e.kind === "boss" ? 0.6 : 0.16)
        break
      }
      case "hurt":
        this.hurtFlash = Math.min(1, this.hurtFlash + 0.5)
        this.shake(7, 0.22)
        break
      case "levelup":
        this.flash = Math.max(this.flash, 0.30)
        break
      case "merge":
        this.addFloat(e.x, e.y - 40, "★" + e.stars, tierColor(e.stars), 18)
        this.flash = Math.max(this.flash, 0.18)
        this.addShock(e.x, e.y, 120, tierColor(e.stars))
        break
      case "death":
        this.flash = 0.7
        break
      default:
        break
    }
  }

  private shake(mag: number, t: number): void {
    this.shakeMag = Math.max(this.shakeMag, mag)
    this.shakeT = Math.max(this.shakeT, t)
  }

  sync(sim: Sim, dt: number): void {
    const p = sim.player
    // —— 相机 ——
    const zoom = this.zoom
    const camX = p.x
    const camY = p.y
    let sx = 0, sy = 0
    if (this.shakeT > 0) {
      this.shakeT = Math.max(0, this.shakeT - dt)
      const m = this.shakeMag * (this.shakeT / 0.6)
      sx = Math.sin(sim.tick * 3.1) * m
      sy = Math.cos(sim.tick * 4.3) * m
    } else {
      this.shakeMag = 0
    }
    this.camera.scale.set(zoom)
    this.camera.position.set(this.viewW / 2 - camX * zoom + sx, this.viewH / 2 - camY * zoom + sy)
    this.bg.update(camX, camY)

    // —— 法术场 ——
    this.fieldLayer.begin()
    for (const f of sim.fields) {
      const def = ["well", "repulse", "rift"].includes(f.weapon) ? f.weapon : "well"
      const s = this.fieldLayer.take(this.tex.field[def])
      s.position.set(f.x, f.y)
      s.width = f.r * 2
      s.height = f.r * 2
      const k = f.life / f.maxLife
      s.alpha = 0.30 + 0.55 * Math.min(1, k * 2.2)
      s.rotation = sim.tick * 0.004 * (f.weapon === "repulse" ? -1 : 1)
      s.blendMode = "add"
    }
    this.fieldLayer.end()

    // —— 掉落 ——
    this.dropLayer.begin()
    for (const d of sim.drops) {
      const tex = d.kind === "coin" ? this.tex.coin : d.kind === "xp" ? this.tex.xp : d.kind === "health" ? this.tex.health : this.tex.weapon[d.weapon ?? ""] ?? this.tex.coin
      const s = this.dropLayer.take(tex)
      const bob = Math.sin(d.t * 3 + d.id) * 2
      s.position.set(d.x, d.y + bob)
      if (d.kind === "weapon") { s.width = 40; s.height = 40 } else { s.width = 30; s.height = 30 }
      s.rotation = d.t * 0.7
      s.blendMode = d.kind === "xp" || d.kind === "weapon" ? "add" : "normal"
    }
    this.dropLayer.end()

    // —— 敌人 ——
    this.enemyLayer.begin()
    for (const e of sim.enemies) {
      const s = this.enemyLayer.take(this.tex.enemy[e.kind])
      s.position.set(e.x, e.y)
      const scale = e.r / ({ scout: 13, drone: 16, heavy: 22, boss: 46 }[e.kind])
      s.scale.set(scale)
      s.rotation = Math.atan2(p.y - e.y, p.x - e.x) - Math.PI / 2
      const hurt = Math.max(0, e.hp / e.maxHp)
      if (hurt < 0.999) s.tint = 0xffffff
      if (hurt < 0.4) s.alpha = 0.92
    }
    this.enemyLayer.end()

    // —— 弹药 ——
    this.bulletLayer.begin()
    for (const b of sim.bullets) {
      const s = this.bulletLayer.take(this.tex.bullet)
      s.position.set(b.x, b.y)
      s.rotation = Math.atan2(b.vy, b.vx)
      s.width = 26; s.height = 14
      s.blendMode = "add"
    }
    for (const b of sim.eshots) {
      const s = this.bulletLayer.take(this.tex.eshot)
      s.position.set(b.x, b.y)
      s.width = 24; s.height = 24
      s.blendMode = "add"
    }
    this.bulletLayer.end()

    // —— 粒子 ——
    this.particleLayer.begin()
    for (const q of sim.particles) {
      const s = this.particleLayer.take(this.tex.px)
      s.position.set(q.x, q.y)
      const k = q.life / q.maxLife
      s.width = q.size * 2.6 * k + 1
      s.height = q.size * 2.6 * k + 1
      s.tint = q.color
      s.alpha = Math.min(1, k * 1.4)
      s.rotation = q.life * 6
      s.blendMode = "add"
    }
    this.particleLayer.end()

    // —— 玩家舰 ——
    this.shipLayer.begin()
    const ship = this.shipLayer.take(this.tex.ship)
    ship.position.set(p.x, p.y)
    ship.rotation = p.facing + Math.PI / 2
    ship.scale.set(1.18)
    if (sim.afterburn > 0) { ship.tint = 0xfff2d0 }
    if (p.invuln > 0 && Math.floor(sim.tick / 4) % 2 === 0) ship.alpha = 0.45
    this.shipLayer.end()

    // —— 护盾环 ——
    // （护盾期间在船外画一圈，用冲击环机制重用）

    // —— 飘字 ——
    for (let i = this.floats.length - 1; i >= 0; i--) {
      const f = this.floats[i]
      f.life -= dt
      f.t.y += f.vy * dt
      f.t.alpha = Math.max(0, f.life / f.maxLife)
      if (f.life <= 0) { f.t.destroy(); this.floatLayer.removeChild(f.t); this.floats.splice(i, 1) }
    }

    // —— 冲击环 ——
    for (let i = this.shocks.length - 1; i >= 0; i--) {
      const s = this.shocks[i]
      s.life -= dt
      const k = 1 - s.life / s.maxLife
      s.g.clear()
      s.g.circle(0, 0, s.r * (0.35 + k * 0.95)).stroke({ width: 2.5 * (1 - k) + 0.6, color: s.color, alpha: Math.max(0, 0.7 * (1 - k)) })
      s.g.circle(0, 0, s.r * (0.35 + k * 0.95) * 1.35).stroke({ width: 1.2 * (1 - k), color: s.color, alpha: Math.max(0, 0.28 * (1 - k)) })
      if (s.life <= 0) { s.g.destroy(); this.worldFx.removeChild(s.g); this.shocks.splice(i, 1) }
    }

    this.flash = Math.max(0, this.flash - dt * 2.2)
    this.hurtFlash = Math.max(0, this.hurtFlash - dt * 1.6)
  }

  /** 全屏闪光强度（升级 / Boss 击杀），由宿主叠加到 HUD 层 */
  get screenFlash(): number { return this.flash }
  get hurtAmount(): number { return this.hurtFlash }

  destroy(): void {
    this.stage.destroy({ children: true })
    this.floats = []
    this.shocks = []
  }
}
