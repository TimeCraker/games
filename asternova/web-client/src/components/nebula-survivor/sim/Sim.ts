import { ENEMIES } from "../content/enemies"
import { DEFAULT_ARENA, type ArenaDef, type Obstacle } from "../content/arena"
import { CLASSES, type ClassDef } from "../content/classes"
import { ESKILLS } from "../content/eskills"
import { MERGE_REQUIRED, MAX_STARS, WEAPONS, upgradeCost, weaponDamage, weaponRange } from "../content/weapons"
import { Rng } from "./rng"
import type {
  BulletState, ClassId, DropKind, DropState, EnemyShotState, EnemyState,
  ESkillId, FieldState, ParticleState, PlayerState, SimEvent, Vec, WeaponId, WeaponSlot,
} from "./types"

/** 固定步长：模拟永远以这个 dt 前进，与渲染帧率完全解耦（白皮书 §11.1） */
export const FIXED_DT = 1 / 60
/** 单帧最多补多少步，防止切后台回来炸帧 */
export const MAX_CATCHUP_STEPS = 5

const MAX_ENEMIES = 420
const MAX_BULLETS = 320
const MAX_ESHOTS = 260
const MAX_DROPS = 220
const MAX_FIELDS = 24

/** 波次时长（秒）；每波结束给一次商店机会 */
export const WAVE_SECONDS = 42
/** 每局固定 Boss 波 */
export const BOSS_WAVES = [5, 10, 15]

export type SimOptions = {
  seed: number
  classId: ClassId
  /** 局外加成（来自 save.ts） */
  bonus?: { damage?: number; armor?: number; spell?: number; eskillLevel?: number; startWeaponStars?: Partial<Record<WeaponId, number>> }
}

export class Sim {
  readonly arena: ArenaDef
  readonly cls: ClassDef
  readonly rng: Rng
  readonly seed: number

  time = 0
  tick = 0
  wave = 1
  waveT = 0
  kills = 0
  score = 0
  coins = 0
  xp = 0
  level = 1
  xpToNext = 26
  gameOver = false
  /** 商店开启中（模拟暂停推进由外层控制） */
  shopOpen = false
  shopRefreshFree = 1
  shopOffers: WeaponId[] = []
  bossAlive = false

  readonly player: PlayerState
  weapons: WeaponSlot[] = []
  enemies: EnemyState[] = []
  bullets: BulletState[] = []
  eshots: EnemyShotState[] = []
  drops: DropState[] = []
  fields: FieldState[] = []
  particles: ParticleState[] = []

  /** E 技状态 */
  eskill: ESkillId
  eskillCd = 0
  eskillLevel: number
  afterburn = 0
  quantumArmed = false

  /** 局外加成 */
  private bonusDmg: number
  private bonusArmor: number
  private bonusSpell: number

  /** 事件出口：渲染/音效消费，**不回流进模拟** */
  onEvent: ((e: SimEvent) => void) | null = null

  private inputX = 0
  private inputY = 0
  private nextId = 1
  private moveSpeed: number
  private dpsAcc = 0
  private dpsT = 0
  private dpsValue = 0

  constructor(opts: SimOptions) {
    this.seed = opts.seed
    this.rng = new Rng(opts.seed)
    this.arena = DEFAULT_ARENA
    this.cls = CLASSES[opts.classId]
    this.eskill = this.cls.eskill
    this.eskillLevel = opts.bonus?.eskillLevel ?? 1
    this.bonusDmg = opts.bonus?.damage ?? 0
    this.bonusArmor = opts.bonus?.armor ?? 0
    this.bonusSpell = opts.bonus?.spell ?? 0

    this.player = {
      x: 0, y: 0, vx: 0, vy: 0,
      hp: this.cls.maxHp, maxHp: this.cls.maxHp, r: 15,
      invuln: 1.2, facing: -Math.PI / 2,
      shield: 0, quantumMark: null,
    }
    this.moveSpeed = this.cls.speed

    // 开局武器 = 职业第一把，1★
    const first = this.cls.weapons[0]
    this.weapons.push({ id: first, stars: opts.bonus?.startWeaponStars?.[first] ?? 1, mergeCount: 0, cooldown: 0 })
    this.refreshShop()
  }

  /* ============================ 输入 ============================ */

  setMove(x: number, y: number): void {
    const m = Math.hypot(x, y)
    if (m > 1) { x /= m; y /= m }
    this.inputX = x
    this.inputY = y
  }

  triggerESkill(): void {
    if (this.gameOver || this.eskillCd > 0) return
    const def = ESKILLS[this.eskill]
    const p = this.player
    switch (this.eskill) {
      case "blink": {
        const d = (def.amount ?? 180) * (1 + (this.eskillLevel - 1) * 0.12)
        const a = (Math.abs(this.inputX) + Math.abs(this.inputY) > 0.01)
          ? Math.atan2(this.inputY, this.inputX)
          : p.facing
        this.tryMove(p, Math.cos(a) * d, Math.sin(a) * d, true)
        p.invuln = Math.max(p.invuln, def.duration ?? 0.25)
        break
      }
      case "shield":
        p.shield = (def.duration ?? 3) * (1 + (this.eskillLevel - 1) * 0.10)
        break
      case "afterburn":
        this.afterburn = (def.duration ?? 3) * (1 + (this.eskillLevel - 1) * 0.08)
        break
      case "recharge":
        this.heal((def.amount ?? 36) * (1 + (this.eskillLevel - 1) * 0.18))
        break
      case "quantum": {
        if (!this.quantumArmed || !p.quantumMark) {
          p.quantumMark = { x: p.x, y: p.y }
          this.quantumArmed = true
          p.invuln = Math.max(p.invuln, 0.4)
        } else {
          this.tryMove(p, p.quantumMark.x - p.x, p.quantumMark.y - p.y, true)
          p.quantumMark = null
          this.quantumArmed = false
          p.invuln = Math.max(p.invuln, 0.6)
        }
        break
      }
    }
    this.eskillCd = def.cd * (1 - Math.min(0.35, (this.eskillLevel - 1) * 0.06))
    this.emit({ type: "eskill", x: p.x, y: p.y, id: this.eskill })
  }

  /* ============================ 主循环 ============================ */

  /** 推进固定步长。dt 必须等于 FIXED_DT —— 由调用方用累加器保证。 */
  step(): void {
    if (this.gameOver || this.shopOpen) return
    const dt = FIXED_DT
    this.tick++
    this.time += dt
    this.waveT += dt

    this.stepPlayer(dt)
    this.stepWeapons(dt)
    if (this.shopOpen) return // 商店在波次切换时开启，本步不再推进战斗
    this.stepEnemies(dt)
    this.stepBullets(dt)
    this.stepFields(dt)
    this.stepDrops(dt)
    this.stepParticles(dt)
    this.stepWaves(dt)
  }

  private stepPlayer(dt: number): void {
    const p = this.player
    const spd = this.moveSpeed * (this.afterburn > 0 ? 1.8 : 1)
    const tx = this.inputX * spd
    const ty = this.inputY * spd
    // 加速度趋近，手感比瞬时速度更「有重量」
    const k = Math.min(1, dt * 14)
    p.vx += (tx - p.vx) * k
    p.vy += (ty - p.vy) * k
    this.tryMove(p, p.vx * dt, p.vy * dt, false)

    // 朝向：优先看最近敌人（自动索敌，玩家只负责走位）
    const t = this.nearestEnemy()
    if (t) p.facing = Math.atan2(t.y - p.y, t.x - p.x)
    else if (Math.hypot(p.vx, p.vy) > 8) p.facing = Math.atan2(p.vy, p.vx)

    p.invuln = Math.max(0, p.invuln - dt)
    p.shield = Math.max(0, p.shield - dt)
    this.afterburn = Math.max(0, this.afterburn - dt)
    this.eskillCd = Math.max(0, this.eskillCd - dt)
  }

  private stepWeapons(dt: number): void {
    const p = this.player
    for (const w of this.weapons) {
      w.cooldown -= dt
      if (w.cooldown > 0) continue
      const def = WEAPONS[w.id]
      w.cooldown = def.cd
      const dmg = weaponDamage(def, w.stars) * this.cls.dmgMul * (1 + this.bonusDmg) *
        (def.kind === "field" ? this.cls.spellMul * (1 + this.bonusSpell) : 1)
      const range = weaponRange(def, w.stars)
      const target = this.nearestEnemy()

      if (def.kind === "ranged") {
        if (!target) { w.cooldown = 0.05; continue }
        const base = Math.atan2(target.y - p.y, target.x - p.x)
        const shots = w.id === "scatter" ? 3 + Math.min(4, w.stars) : 1
        for (let i = 0; i < shots; i++) {
          const spread = shots > 1 ? (i - (shots - 1) / 2) * 0.14 : 0
          const a = base + spread
          this.spawnBullet(p.x + Math.cos(a) * p.r, p.y + Math.sin(a) * p.r, a, def.speed, dmg, def.pierce, range / def.speed)
        }
        this.emit({ type: "shoot", x: p.x, y: p.y, ang: base, kind: "ranged" })
      } else if (def.kind === "melee") {
        if (w.id === "blade") {
          // 回旋刃：环绕船体的旋转刃，按角速度命中周围敌人
          const hits = this.enemiesWithin(p.x, p.y, range)
          for (const e of hits) this.damageEnemy(e, dmg * dt * 6, false)
        } else {
          if (!target) { w.cooldown = 0.08; continue }
          const hits = this.enemiesWithin(p.x, p.y, range)
            .filter((e) => {
              const a = Math.atan2(e.y - p.y, e.x - p.x)
              let d = Math.abs(((a - p.facing + Math.PI) % (Math.PI * 2)) - Math.PI)
              d = Math.min(d, Math.abs(d - Math.PI * 2))
              return d < def.speed / 2 // speed 作为挥击张角（弧度）
            })
          for (const e of hits) {
            this.damageEnemy(e, dmg, false)
            if (w.id === "hook") {
              const a = Math.atan2(p.y - e.y, p.x - e.x)
              e.x += Math.cos(a) * 46
              e.y += Math.sin(a) * 46
            } else if (w.id === "ram") {
              const a = Math.atan2(e.y - p.y, e.x - p.x)
              e.x += Math.cos(a) * 54
              e.y += Math.sin(a) * 54
            }
          }
          this.emit({ type: "shoot", x: p.x, y: p.y, ang: p.facing, kind: "melee" })
        }
      } else {
        // 法术：在地上/空间放一个场
        const atPlayer = w.id === "repulse"
        const ox = atPlayer ? p.x : p.x + Math.cos(p.facing) * Math.min(range * 0.9, 150)
        const oy = atPlayer ? p.y : p.y + Math.sin(p.facing) * Math.min(range * 0.9, 150)
        this.fields.push({
          id: this.nextId++, weapon: w.id, x: ox, y: oy, r: range,
          life: def.speed, maxLife: def.speed,
          dmgPerSec: dmg * (def.dpsMul ?? 1), pull: def.pull ?? 0,
        })
        if (this.fields.length > MAX_FIELDS) this.fields.shift()
        this.emit({ type: "shoot", x: ox, y: oy, ang: p.facing, kind: "field" })
      }
    }
  }

  private stepEnemies(dt: number): void {
    const p = this.player
    for (let i = this.enemies.length - 1; i >= 0; i--) {
      const e = this.enemies[i]
      const def = ENEMIES[e.kind]
      let ax = p.x - e.x, ay = p.y - e.y
      const d = Math.hypot(ax, ay) || 1
      ax /= d; ay /= d
      // 引力井吸附
      if (e.pull > 0) {
        for (const f of this.fields) {
          if (f.pull === 0) continue
          const fx = f.x - e.x, fy = f.y - e.y
          const fd = Math.hypot(fx, fy)
          if (fd < f.r) {
            const s = (1 - fd / f.r) * (f.pull / 220)
            e.x += (fx / (fd || 1)) * s * dt * 60
            e.y += (fy / (fd || 1)) * s * dt * 60
          }
        }
      }
      e.vx = ax * e.speed
      e.vy = ay * e.speed
      this.tryMove(e, e.vx * dt, e.vy * dt, false, e.r)

      e.touchCd = Math.max(0, e.touchCd - dt)
      if (d < e.r + p.r && e.touchCd <= 0) {
        e.touchCd = def.touchCd
        this.hurt(e.dmg)
      }

      if (def.shooter) {
        e.shootCd = Math.max(0, e.shootCd - dt)
        if (e.shootCd <= 0 && d < 620) {
          e.shootCd = e.kind === "boss" ? 0.55 : 1.6
          const spread = e.kind === "boss" ? 5 : 1
          for (let s = 0; s < spread; s++) {
            const a = Math.atan2(ay, ax) + (s - (spread - 1) / 2) * 0.18
            this.eshots.push({
              id: this.nextId++, x: e.x, y: e.y,
              vx: Math.cos(a) * 210, vy: Math.sin(a) * 210,
              r: e.kind === "boss" ? 9 : 6, dmg: Math.round(e.dmg * 0.7), life: 4.5,
            })
          }
          if (this.eshots.length > MAX_ESHOTS) this.eshots.splice(0, this.eshots.length - MAX_ESHOTS)
        }
      }
      if (e.hp <= 0) this.killEnemy(e, i)
    }
  }

  private stepBullets(dt: number): void {
    for (let i = this.bullets.length - 1; i >= 0; i--) {
      const b = this.bullets[i]
      b.x += b.vx * dt; b.y += b.vy * dt; b.life -= dt
      if (b.life <= 0 || this.blocked(b.x, b.y, b.r)) { this.bullets.splice(i, 1); continue }
      for (const e of this.enemies) {
        if (b.hit.includes(e.id)) continue
        if (Math.hypot(e.x - b.x, e.y - b.y) < e.r + b.r) {
          this.damageEnemy(e, b.dmg, false)
          b.hit.push(e.id)
          if (b.pierce <= 0) { this.bullets.splice(i, 1); break }
          b.pierce--
        }
      }
    }
    const p = this.player
    for (let i = this.eshots.length - 1; i >= 0; i--) {
      const s = this.eshots[i]
      s.x += s.vx * dt; s.y += s.vy * dt; s.life -= dt
      if (s.life <= 0 || this.blocked(s.x, s.y, s.r)) { this.eshots.splice(i, 1); continue }
      if (Math.hypot(p.x - s.x, p.y - s.y) < p.r + s.r) {
        this.hurt(s.dmg)
        this.eshots.splice(i, 1)
      }
    }
  }

  private stepFields(dt: number): void {
    for (let i = this.fields.length - 1; i >= 0; i--) {
      const f = this.fields[i]
      f.life -= dt
      if (f.life <= 0) { this.fields.splice(i, 1); continue }
      for (const e of this.enemies) {
        if (Math.hypot(e.x - f.x, e.y - f.y) < f.r + e.r) {
          this.damageEnemy(e, f.dmgPerSec * dt, false)
        }
      }
    }
  }

  private stepDrops(dt: number): void {
    const p = this.player
    for (let i = this.drops.length - 1; i >= 0; i--) {
      const d = this.drops[i]
      d.t += dt
      const dx = p.x - d.x, dy = p.y - d.y
      const dist = Math.hypot(dx, dy) || 1
      if (dist < 190) {
        const pull = 260 / dist
        d.vx += (dx / dist) * pull * dt * 12
        d.vy += (dy / dist) * pull * dt * 12
      }
      d.vx *= 0.94; d.vy *= 0.94
      d.x += d.vx * dt; d.y += d.vy * dt
      if (dist < p.r + 14) { this.collect(d); this.drops.splice(i, 1) }
    }
  }

  private stepParticles(dt: number): void {
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const q = this.particles[i]
      q.life -= dt
      if (q.life <= 0) { this.particles.splice(i, 1); continue }
      q.x += q.vx * dt; q.y += q.vy * dt
      q.vx *= 0.965; q.vy *= 0.965
    }
  }

  private stepWaves(dt: number): void {
    // 持续刷怪：刷新速率随波次上升
    this.spawnAcc += dt * (2.2 + this.wave * 1.15)
    while (this.spawnAcc >= 1 && this.enemies.length < MAX_ENEMIES) {
      this.spawnAcc -= 1
      this.spawnEnemy()
    }
    if (this.waveT >= WAVE_SECONDS) {
      this.waveT = 0
      this.wave++
      this.emit({ type: "wave", wave: this.wave })
      this.openShop()
    }
    if (BOSS_WAVES.includes(this.wave) && !this.bossAlive && this.waveT < 0.2) this.spawnBoss()
  }
  private spawnAcc = 0

  /* ============================ 实体操作 ============================ */

  private spawnEnemy(): void {
    const w = this.wave
    const roll = this.rng.f()
    let kind: EnemyState["kind"] = "scout"
    if (w >= 3 && roll > 0.62) kind = "drone"
    if (w >= 5 && roll > 0.88) kind = "heavy"
    const def = ENEMIES[kind]
    const pos = this.edgeSpawnPoint()
    const hp = def.hp * (1 + (w - 1) * 0.22)
    this.enemies.push({
      id: this.nextId++, kind, x: pos.x, y: pos.y, vx: 0, vy: 0,
      hp, maxHp: hp, r: def.r, speed: def.speed * (1 + (w - 1) * 0.03),
      dmg: def.dmg * (1 + (w - 1) * 0.12), pull: 0,
      touchCd: 0, shootCd: this.rng.range(0.4, 1.8),
    })
  }

  private spawnBoss(): void {
    const def = ENEMIES.boss
    const hp = def.hp * (1 + (this.wave / BOSS_WAVES[0] - 1) * 0.5)
    const pos = this.edgeSpawnPoint()
    this.enemies.push({
      id: this.nextId++, kind: "boss", x: pos.x, y: pos.y, vx: 0, vy: 0,
      hp, maxHp: hp, r: def.r, speed: def.speed, dmg: def.dmg, pull: 0,
      touchCd: 0, shootCd: 1.2,
    })
    this.bossAlive = true
  }

  /** 在竞技场边缘、且离玩家足够远的点上刷出 */
  private edgeSpawnPoint(): Vec {
    const { halfW, halfH } = this.arena
    const p = this.player
    for (let i = 0; i < 12; i++) {
      const side = this.rng.int(0, 3)
      const t = this.rng.range(-0.9, 0.9)
      const x = side === 0 ? -halfW * 0.94 : side === 1 ? halfW * 0.94 : t * halfW
      const y = side === 2 ? -halfH * 0.94 : side === 3 ? halfH * 0.94 : t * halfH
      if (Math.hypot(x - p.x, y - p.y) > this.arena.safeR) return { x, y }
    }
    return { x: -halfW * 0.94, y: 0 }
  }

  private spawnBullet(x: number, y: number, a: number, speed: number, dmg: number, pierce: number, life: number): void {
    this.bullets.push({
      id: this.nextId++, x, y, vx: Math.cos(a) * speed, vy: Math.sin(a) * speed,
      r: 4, dmg, life, pierce, hit: [],
    })
    if (this.bullets.length > MAX_BULLETS) this.bullets.shift()
  }

  damageEnemy(e: EnemyState, amount: number, crit: boolean): void {
    if (e.hp <= 0) return
    e.hp -= amount
    this.dpsAcc += amount
    this.emit({ type: "hit", x: e.x, y: e.y, amount: Math.round(amount), crit })
  }

  private killEnemy(e: EnemyState, index: number): void {
    const def = ENEMIES[e.kind]
    this.enemies.splice(index, 1)
    this.kills++
    this.score += def.score
    if (e.kind === "boss") this.bossAlive = false
    this.emit({ type: "kill", x: e.x, y: e.y, kind: e.kind })
    // 碎块粒子
    for (let i = 0; i < (e.kind === "boss" ? 34 : 7); i++) {
      const u = this.rng.unit()
      this.particles.push({
        x: e.x, y: e.y, vx: u.x * this.rng.range(60, 220), vy: u.y * this.rng.range(60, 220),
        life: this.rng.range(0.35, 0.9), maxLife: 0.9, size: this.rng.range(2, 4.5),
        kind: "shard", color: e.kind === "scout" ? 0xc08069 : e.kind === "drone" ? 0x7fb39e : 0xc0503a,
      })
    }
    // 掉落
    this.spawnDrop(e.x, e.y, "coin", def.coin)
    this.spawnDrop(e.x + 12, e.y - 8, "xp", def.xp)
    if (this.rng.f() < (e.kind === "boss" ? 1 : 0.018)) this.spawnDrop(e.x + 8, e.y + 10, "health", 22)
    if (e.kind === "boss" || this.rng.f() < 0.055) {
      const pool = this.cls.weapons
      const id = this.rng.pick(pool)
      this.drops.push({ id: this.nextId++, kind: "weapon", x: e.x, y: e.y, vx: 0, vy: 0, value: 0, weapon: id, t: 0 })
    }
  }

  private spawnDrop(x: number, y: number, kind: DropKind, value: number): void {
    if (this.drops.length >= MAX_DROPS) this.drops.shift()
    const u = this.rng.unit()
    this.drops.push({ id: this.nextId++, kind, x, y, vx: u.x * 60, vy: u.y * 60, value, t: 0 })
  }

  private collect(d: DropState): void {
    this.emit({ type: "pickup", x: d.x, y: d.y, kind: d.kind })
    switch (d.kind) {
      case "coin": this.coins += d.value; break
      case "xp": this.addXp(d.value); break
      case "health": this.heal(d.value); break
      case "weapon": if (d.weapon) this.acquireWeapon(d.weapon); break
    }
  }

  /** 拾取武器：已持有且未满星 → 累计三合一；未持有且有空位 → 新槽 */
  acquireWeapon(id: WeaponId): void {
    const owned = this.weapons.find((w) => w.id === id)
    if (owned) {
      if (owned.stars >= MAX_STARS) { this.coins += 40; return }
      owned.mergeCount++
      if (owned.mergeCount >= MERGE_REQUIRED) {
        owned.mergeCount = 0
        owned.stars++
        this.emit({ type: "merge", x: this.player.x, y: this.player.y, weapon: id, stars: owned.stars })
      }
      return
    }
    if (this.weapons.length < 3) {
      this.weapons.push({ id, stars: 1, mergeCount: 0, cooldown: 0 })
      this.emit({ type: "merge", x: this.player.x, y: this.player.y, weapon: id, stars: 1 })
      return
    }
    this.coins += 40
  }

  /** 花金币直升 1 星（白皮书 §5.3 的第二条路径） */
  upgradeWeapon(id: WeaponId): boolean {
    const w = this.weapons.find((x) => x.id === id)
    if (!w || w.stars >= MAX_STARS) return false
    const cost = upgradeCost(w.stars)
    if (this.coins < cost) return false
    this.coins -= cost
    w.stars++
    this.emit({ type: "merge", x: this.player.x, y: this.player.y, weapon: id, stars: w.stars })
    return true
  }

  private addXp(v: number): void {
    this.xp += v
    while (this.xp >= this.xpToNext) {
      this.xp -= this.xpToNext
      this.level++
      this.xpToNext = Math.round(this.xpToNext * 1.24 + 6)
      // 砍掉「三选一」：升级给固定的小幅基础数值，不做选择界面
      this.player.maxHp += 3
      this.player.hp = Math.min(this.player.maxHp, this.player.hp + 3)
      this.moveSpeed += 0.9
      this.emit({ type: "levelup", level: this.level })
    }
  }

  heal(v: number): void {
    this.player.hp = Math.min(this.player.maxHp, this.player.hp + v)
  }

  hurt(amount: number): void {
    const p = this.player
    if (this.gameOver || p.invuln > 0 || p.shield > 0) return
    const armor = Math.min(0.6, this.cls.armor + this.bonusArmor)
    const real = amount * (1 - armor)
    p.hp -= real
    p.invuln = 0.45
    this.emit({ type: "hurt", x: p.x, y: p.y, amount: Math.round(real) })
    if (p.hp <= 0) { p.hp = 0; this.gameOver = true; this.emit({ type: "death" }) }
  }

  /* ============================ 碰撞 ============================ */

  /** 移动并解算：竞技场边界 + 障碍物 */
  private tryMove(o: { x: number; y: number }, dx: number, dy: number, teleport: boolean, r = this.player.r): void {
    const nx = o.x + dx, ny = o.y + dy
    if (teleport) {
      const c = this.clampToArena(nx, ny, r)
      if (!this.blocked(c.x, c.y, r)) { o.x = c.x; o.y = c.y; return }
    }
    // 分轴解算，贴墙滑动手感更好
    const cx = this.clampToArena(o.x + dx, o.y, r)
    if (!this.blocked(cx.x, cx.y, r)) { o.x = cx.x; o.y = cx.y }
    const cy = this.clampToArena(o.x, o.y + dy, r)
    if (!this.blocked(cy.x, cy.y, r)) { o.x = cy.x; o.y = cy.y }
  }

  private clampToArena(x: number, y: number, r: number): Vec {
    const { halfW, halfH } = this.arena
    return {
      x: Math.max(-halfW + r, Math.min(halfW - r, x)),
      y: Math.max(-halfH + r, Math.min(halfH - r, y)),
    }
  }

  /** 点是否落在障碍物内 */
  private blocked(x: number, y: number, r: number): boolean {
    for (const o of this.arena.obstacles) {
      if (o.kind === "rect") {
        const cx = Math.max(o.x, Math.min(o.x + o.w, x))
        const cy = Math.max(o.y, Math.min(o.y + o.h, y))
        if ((x - cx) ** 2 + (y - cy) ** 2 < r * r) return true
      } else {
        if ((x - o.x) ** 2 + (y - o.y) ** 2 < (o.r + r) ** 2) return true
      }
    }
    return false
  }

  /* ============================ 查询 ============================ */

  nearestEnemy(): EnemyState | null {
    let best: EnemyState | null = null
    let bd = Infinity
    for (const e of this.enemies) {
      const d = (e.x - this.player.x) ** 2 + (e.y - this.player.y) ** 2
      if (d < bd) { bd = d; best = e }
    }
    return best
  }

  enemiesWithin(x: number, y: number, r: number): EnemyState[] {
    const out: EnemyState[] = []
    for (const e of this.enemies) {
      if (Math.hypot(e.x - x, e.y - y) < r + e.r) out.push(e)
    }
    return out
  }

  /* ============================ 商店 ============================ */

  openShop(): void {
    this.shopOpen = true
    this.shopRefreshFree = 1
    this.refreshShop(true)
  }
  closeShop(): void { this.shopOpen = false }

  refreshShop(free = false): void {
    if (!free) {
      if (this.shopRefreshFree > 0) this.shopRefreshFree--
      else {
        const cost = 25 + this.wave * 5
        if (this.coins < cost) return
        this.coins -= cost
      }
    }
    // 只卖本职业可用的 3 把武器
    this.shopOffers = [this.rng.pick(this.cls.weapons), this.rng.pick(this.cls.weapons), this.rng.pick(this.cls.weapons)]
  }

  buyWeapon(id: WeaponId): boolean {
    const cost = 45 + this.wave * 6
    if (this.coins < cost) return false
    if (this.weapons.length >= 3 && !this.weapons.some((w) => w.id === id)) return false
    this.coins -= cost
    this.acquireWeapon(id)
    return true
  }

  /* ============================ 快照 / 测试支撑 ============================ */

  /** 累计伤害 / 时间 → 每秒伤害（结算展示用） */
  get dps(): number { return this.dpsValue }
  tickDps(dt: number): void {
    this.dpsT += dt
    if (this.dpsT >= 0.5) { this.dpsValue = this.dpsAcc / this.dpsT; this.dpsAcc = 0; this.dpsT = 0 }
  }

  /** 确定性指纹：同种子 + 同输入 → 完全一致（白皮书 §11.9） */
  hashSnapshot(): number {
    let h = 2166136261
    const push = (n: number) => {
      const v = Math.round(n * 1000)
      h ^= v & 0xffffffff
      h = Math.imul(h, 16777619)
    }
    push(this.tick); push(this.player.x); push(this.player.y); push(this.player.hp)
    push(this.enemies.length); push(this.bullets.length); push(this.drops.length); push(this.kills)
    for (const e of this.enemies) { push(e.id); push(e.x); push(e.y); push(e.hp) }
    for (const w of this.weapons) { push(w.stars); push(w.mergeCount) }
    return h >>> 0
  }

  private emit(e: SimEvent): void { this.onEvent?.(e) }
}

export function obstacleLabel(o: Obstacle): string {
  return o.kind === "rect" ? `rect(${o.w}x${o.h})` : `circle(${o.r})`
}
