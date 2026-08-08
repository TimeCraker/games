/**
 * Nebula Survivor — 核心模拟（Canvas 渲染由 React 层调用 render）
 */

/** 五条独立升级轨道，每次升级三选一，可刷新一次 */
export type UpgradeTrackId =
  | "fire_salvo"
  | "fire_rate"
  | "ring_count"
  | "ring_spin"
  | "afterburner"

export type EnemyTier = 1 | 2 | 3

export interface Enemy {
  id: number
  x: number
  y: number
  vx: number
  vy: number
  hp: number
  maxHp: number
  r: number
  alive: boolean
  tier: EnemyTier
  ringHitCd: number
  pullVx: number
  pullVy: number
  /** 已看见主角或进入感知范围，永久追击 */
  committedAggro: boolean
  /** 屏外生成后短暂朝主角试探，超时后改为游荡直至发现 */
  probeT: number
  /** 游荡转向相位 */
  wanderPhase: number
  /** 追击时的目标速度模长 */
  baseSpd: number
}

export interface Bullet {
  id: number
  x: number
  y: number
  vx: number
  vy: number
  r: number
  dmg: number
  life: number
  alive: boolean
}

export interface Crystal {
  id: number
  x: number
  y: number
  vx: number
  vy: number
  value: number
  r: number
  alive: boolean
}

export interface HealthPack {
  id: number
  x: number
  y: number
  vx: number
  vy: number
  r: number
  alive: boolean
}

export interface BurstParticle {
  x: number
  y: number
  vx: number
  vy: number
  life: number
  maxLife: number
  size: number
  kind: "pink" | "violet" | "white"
}

export interface TrailSpark {
  x: number
  y: number
  life: number
  maxLife: number
  size: number
}

/** 敌人死亡碎块 */
export interface DeathShard {
  x: number
  y: number
  vx: number
  vy: number
  life: number
  maxLife: number
  rot: number
  vr: number
  size: number
  tier: EnemyTier
}

export type UpgradeOffer = {
  id: string
  trackId: UpgradeTrackId
  title: string
  desc: string
  isNew: boolean
  badgeLabel: string
}

const MAX_ENEMIES = 3000
/** reset 后预充能，首帧即刷出一批敌人，避免开局空场 */
const SPAWN_ACC_INITIAL = 11
const MAX_BULLETS = 400
const MAX_PARTICLES = 700
const MAX_CRYSTALS = 320
const MAX_HEALTH_PACKS = 12
/** 单杀掉落期望约 1/122，长期接近「百杀量级」出一个 */
const HEALTH_PACK_CHANCE = 0.0082
/** 进入此距离或出现在屏幕内即永久追击 */
const AGGRO_RANGE = 336
/** 屏外生成后朝主角试探移动的时长（秒），过后改为游荡 */
const PROBE_DURATION_MIN = 1.1
const PROBE_DURATION_MAX = 2.6
/** 试探移动速度相对追击速度的比例 */
const PROBE_SPD_MUL = 0.5
/** 游荡速度相对追击速度的比例 */
const WANDER_SPD_MUL = 0.4
const MAX_SHARDS = 500

const TRACK_CAP: Record<UpgradeTrackId, number> = {
  fire_salvo: 6,
  fire_rate: 6,
  ring_count: 12,
  ring_spin: 6,
  afterburner: 6,
}

const ALL_TRACKS: UpgradeTrackId[] = [
  "fire_salvo",
  "fire_rate",
  "ring_count",
  "ring_spin",
  "afterburner",
]

const TRACK_COPY: Record<UpgradeTrackId, { title: string; desc: string }> = {
  fire_salvo: {
    title: "火力覆盖 · 弹幕数量",
    desc: "每次齐射多发射 1 发粉红弹（初始 1，最高 6），共享同一锁定目标并带小幅扇形散布。",
  },
  fire_rate: {
    title: "火力覆盖 · 射速",
    desc: "缩短齐射间隔（最高 6 级）；锁定范围仍随火力等级成长，弹速与单发伤害随双轨总和提升。",
  },
  ring_count: {
    title: "星环粒子 · 数量",
    desc: "增加绕身白光粒子数量（最高 12 颗）；轨道半径随数量成长，粒子越多环伤略增。",
  },
  ring_spin: {
    title: "星环粒子 · 转速",
    desc: "提高环绕角速度（最高 6 级）；与数量轨独立，伤害加成单独累计。",
  },
  afterburner: {
    title: "星焰推进",
    desc: "提升移动速度（共 6 级：从基础 0.8× 递增至最高 2×）。",
  },
}

const PLAYER_R = 14
const PICKUP_R = 22
const CRYSTAL_R = 5
const BASE_MOVE = 262.5

function dist2(ax: number, ay: number, bx: number, by: number) {
  const dx = ax - bx
  const dy = ay - by
  return dx * dx + dy * dy
}

function len(x: number, y: number) {
  return Math.hypot(x, y) || 1
}

function norm(x: number, y: number): { x: number; y: number } {
  const l = len(x, y)
  return { x: x / l, y: y / l }
}

function tierRoll(worldTier: number): EnemyTier {
  const r = Math.random()
  if (worldTier <= 1) return 1
  if (worldTier === 2) {
    if (r < 0.82) return 1
    return r < 0.97 ? 2 : 3
  }
  if (worldTier <= 4) {
    if (r < 0.45) return 1
    if (r < 0.88) return 2
    return 3
  }
  if (worldTier <= 8) {
    if (r < 0.22) return 1
    if (r < 0.65) return 2
    return 3
  }
  if (r < 0.12) return 1
  if (r < 0.48) return 2
  return 3
}

function tierStats(tier: EnemyTier, worldTier: number) {
  const wt = Math.max(1, worldTier)
  const base = 1 + (wt - 1) * 0.12
  if (tier === 1) {
    return {
      hp: (9 + wt * 1.1) * base,
      r: 6.5,
      spd: 38 + wt * 2.2,
    }
  }
  if (tier === 2) {
    return {
      hp: (22 + wt * 2.4) * base,
      r: 8.5,
      spd: 44 + wt * 2.8,
    }
  }
  return {
    hp: (48 + wt * 4) * base,
    r: 11,
    spd: 50 + wt * 3.2,
  }
}

export class EntityManager {
  enemies: Enemy[] = []
  nextEnemyId = 1

  clear() {
    this.enemies.length = 0
    this.nextEnemyId = 1
  }

  spawnOutsideView(
    px: number,
    py: number,
    halfW: number,
    halfH: number,
    margin: number,
    hp: number,
    r: number,
    spd: number,
    tier: EnemyTier,
  ) {
    if (this.enemies.length >= MAX_ENEMIES) return
    const side = Math.floor(Math.random() * 4)
    let x = px
    let y = py
    const m = margin + 40
    if (side === 0) {
      x = px + (Math.random() * 2 - 1) * halfW
      y = py - halfH - m
    } else if (side === 1) {
      x = px + (Math.random() * 2 - 1) * halfW
      y = py + halfH + m
    } else if (side === 2) {
      x = px - halfW - m
      y = py + (Math.random() * 2 - 1) * halfH
    } else {
      x = px + halfW + m
      y = py + (Math.random() * 2 - 1) * halfH
    }
    this.enemies.push({
      id: this.nextEnemyId++,
      x,
      y,
      vx: 0,
      vy: 0,
      hp,
      maxHp: hp,
      r,
      alive: true,
      tier,
      ringHitCd: 0,
      pullVx: 0,
      pullVy: 0,
      committedAggro: false,
      probeT: PROBE_DURATION_MIN + Math.random() * (PROBE_DURATION_MAX - PROBE_DURATION_MIN),
      wanderPhase: Math.random() * Math.PI * 2,
      baseSpd: spd,
    })
  }

  removeDead() {
    this.enemies = this.enemies.filter((e) => e.alive)
  }
}

export class NebulaEngine {
  w = 800
  h = 600
  dpr = 1

  player = {
    x: 0,
    y: 0,
    vx: 0,
    vy: 0,
    hp: 100,
    maxHp: 100,
    r: PLAYER_R,
    xp: 0,
    level: 1,
    xpToNext: 32,
    invuln: 0,
  }

  moveX = 0
  moveY = 0

  /** 各轨道当前等级（未满级时可出现在三选一里） */
  upgrades: Record<UpgradeTrackId, number> = {
    fire_salvo: 1,
    fire_rate: 1,
    ring_count: 0,
    ring_spin: 0,
    afterburner: 0,
  }

  /** 本次升级界面剩余刷新次数（开局 level up 设为 1） */
  upgradeRerollsLeft = 0

  bullets: Bullet[] = []
  nextBulletId = 1

  crystals: Crystal[] = []
  nextCrystalId = 1

  healthPacks: HealthPack[] = []
  nextHealthPackId = 1

  particles: BurstParticle[] = []
  trails: TrailSpark[] = []
  shards: DeathShard[] = []

  em = new EntityManager()

  gameTime = 0
  spawnAcc = 0
  laserAcc = 0

  score = 0
  kills = 0

  pausedUpgrade = false
  upgradeChoices: UpgradeOffer[] = []

  gameOver = false

  /** React 规则弹窗打开时为 true，暂停模拟 */
  rulesFrozen = false

  mouseWorldX = 0
  mouseWorldY = 0
  useMouseMove = false

  hitFlash = 0
  hitShake = 0
  /** 受击击退速度（衰减） */
  knockVx = 0
  knockVy = 0
  private trailAcc = 0

  constructor() {
    this.reset()
  }

  /** 全局难度档：约每 60s 现实时间 +1（与得分无关，避免开局爆炸） */
  worldDifficultyTier(): number {
    return Math.min(16, 1 + Math.floor(this.gameTime / 60))
  }

  /** 每秒生成数量上限随难度缓升 */
  private spawnRatePerSec(): number {
    const wt = this.worldDifficultyTier()
    const scoreBoost = Math.min(5, this.score / 9000)
    // 开局约 1.35/s，前几分钟场上更饱满
    return Math.min(36, 1.35 + (wt - 1) * 0.46 + scoreBoost)
  }

  reset() {
    this.player = {
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      hp: 82,
      maxHp: 82,
      r: PLAYER_R,
      xp: 0,
      level: 1,
      xpToNext: 32,
      invuln: 0,
    }
    this.moveX = 0
    this.moveY = 0
    this.upgrades = {
      fire_salvo: 1,
      fire_rate: 1,
      ring_count: 0,
      ring_spin: 0,
      afterburner: 0,
    }
    this.upgradeRerollsLeft = 0
    this.bullets = []
    this.nextBulletId = 1
    this.crystals = []
    this.nextCrystalId = 1
    this.healthPacks = []
    this.nextHealthPackId = 1
    this.particles = []
    this.trails = []
    this.shards = []
    this.em.clear()
    this.gameTime = 0
    this.spawnAcc = SPAWN_ACC_INITIAL
    this.laserAcc = 0
    this.score = 0
    this.kills = 0
    this.pausedUpgrade = false
    this.upgradeChoices = []
    this.gameOver = false
    this.trailAcc = 0
    this.hitFlash = 0
    this.hitShake = 0
    this.knockVx = 0
    this.knockVy = 0
  }

  trackLevel(id: UpgradeTrackId): number {
    return this.upgrades[id]
  }

  /** 移速倍率：基础 0.8×，推进器每级 +0.2，6 级到 2.0× */
  moveSpeedMultiplier(): number {
    const lv = this.upgrades.afterburner
    return 0.8 + (Math.min(TRACK_CAP.afterburner, lv) / TRACK_CAP.afterburner) * 1.2
  }

  private bumpTrack(id: UpgradeTrackId) {
    const cap = TRACK_CAP[id]
    const cur = this.upgrades[id]
    if (cur >= cap) {
      this.player.hp = Math.min(this.player.maxHp, this.player.hp + 22)
      return
    }
    this.upgrades[id] = cur + 1
  }

  pushParticles(x: number, y: number, count: number, spread = 1.2) {
    const kinds: BurstParticle["kind"][] = ["pink", "violet", "white"]
    for (let i = 0; i < count && this.particles.length < MAX_PARTICLES; i++) {
      const a = Math.random() * Math.PI * 2
      const sp = (80 + Math.random() * 220) * spread
      this.particles.push({
        x,
        y,
        vx: Math.cos(a) * sp,
        vy: Math.sin(a) * sp,
        life: 0.35 + Math.random() * 0.45,
        maxLife: 0.8,
        size: 1.5 + Math.random() * 3.5,
        kind: kinds[Math.floor(Math.random() * kinds.length)]!,
      })
    }
  }

  pushDeathShards(x: number, y: number, tier: EnemyTier, baseR: number) {
    const n = 10 + Math.floor(baseR * 0.8)
    for (let i = 0; i < n && this.shards.length < MAX_SHARDS; i++) {
      const a = Math.random() * Math.PI * 2
      const sp = 120 + Math.random() * 280
      this.shards.push({
        x,
        y,
        vx: Math.cos(a) * sp,
        vy: Math.sin(a) * sp,
        life: 0,
        maxLife: 0.28 + Math.random() * 0.22,
        rot: Math.random() * Math.PI * 2,
        vr: (Math.random() - 0.5) * 14,
        size: 2.5 + Math.random() * (3 + tier * 1.2),
        tier,
      })
    }
  }

  killEnemy(e: Enemy, scoreAdd: number, crystalMin: number, crystalMax: number) {
    e.alive = false
    this.kills++
    this.score += scoreAdd
    this.pushParticles(e.x, e.y, 8 + e.tier * 4, 1)
    this.pushDeathShards(e.x, e.y, e.tier, e.r)
    const cv = crystalMin + Math.floor(Math.random() * (crystalMax - crystalMin + 1))
    this.spawnCrystal(e.x, e.y, cv)
    if (Math.random() < HEALTH_PACK_CHANCE) this.spawnHealthPack(e.x, e.y)
  }

  tryLevelUp() {
    if (this.pausedUpgrade || this.gameOver) return
    const p = this.player
    if (p.xp < p.xpToNext) return
    p.xp -= p.xpToNext
    p.level++
    p.xpToNext = Math.floor(32 + p.level * 18 + p.level * p.level * 0.35)
    p.maxHp += 3
    p.hp = Math.min(p.maxHp, p.hp + 8)
    this.rollUpgradeChoices()
    this.pausedUpgrade = true
  }

  /** 打开升级界面时调用：三选一 + 赋予 1 次刷新 */
  rollUpgradeChoices() {
    this.upgradeRerollsLeft = 1
    this.fillUpgradeChoices()
  }

  /** 消耗唯一一次刷新，重新抽三张（未满级轨道） */
  rerollUpgradeChoices(): boolean {
    if (this.upgradeRerollsLeft < 1) return false
    this.upgradeRerollsLeft = 0
    this.fillUpgradeChoices()
    return true
  }

  private fillUpgradeChoices() {
    const available = ALL_TRACKS.filter((id) => this.upgrades[id] < TRACK_CAP[id])
    const shuffled = [...available].sort(() => Math.random() - 0.5)
    const chosen = shuffled.slice(0, Math.min(3, shuffled.length))
    this.upgradeChoices = chosen.map((trackId) => {
      const cur = this.upgrades[trackId]
      const cap = TRACK_CAP[trackId]
      const copy = TRACK_COPY[trackId]
      const next = cur + 1
      return {
        id: trackId,
        trackId,
        title: copy.title,
        desc: copy.desc,
        isNew: cur === 0,
        badgeLabel: cur >= cap ? "MAX" : `${next}/${cap}`,
      }
    })
    if (this.upgradeChoices.length === 0) {
      this.player.hp = Math.min(this.player.maxHp, this.player.hp + 28)
      this.pausedUpgrade = false
    }
  }

  pickUpgrade(offer: UpgradeOffer) {
    this.bumpTrack(offer.trackId)
    this.upgradeRerollsLeft = 0
    this.pausedUpgrade = false
    this.upgradeChoices = []
    this.tryLevelUp()
  }

  private spawnCrystal(x: number, y: number, value: number) {
    if (this.crystals.length >= MAX_CRYSTALS) return
    const a = Math.random() * Math.PI * 2
    this.crystals.push({
      id: this.nextCrystalId++,
      x,
      y,
      vx: Math.cos(a) * 40,
      vy: Math.sin(a) * 40,
      value,
      r: CRYSTAL_R,
      alive: true,
    })
  }

  private spawnHealthPack(x: number, y: number) {
    if (this.healthPacks.length >= MAX_HEALTH_PACKS) return
    const a = Math.random() * Math.PI * 2
    this.healthPacks.push({
      id: this.nextHealthPackId++,
      x,
      y,
      vx: Math.cos(a) * 28,
      vy: Math.sin(a) * 28,
      r: 9,
      alive: true,
    })
  }

  /** 激光索敌不超过当前视野（略小于半屏对角线） */
  private laserLockRangeSq(): number {
    const lv = Math.max(this.upgrades.fire_salvo, this.upgrades.fire_rate)
    const halfW = this.w / this.dpr / 2
    const halfH = this.h / this.dpr / 2
    const viewCap = Math.hypot(halfW, halfH) * 0.92
    const r = Math.min(300 + lv * 10, viewCap)
    return r * r
  }

  /** 有目标并成功生成至少一发时返回 true（无敌人时不扣射速冷却） */
  private tryFireLaser(): boolean {
    const salvo = this.upgrades.fire_salvo
    if (salvo < 1) return false
    const sumLv = this.upgrades.fire_salvo + this.upgrades.fire_rate
    const range2 = this.laserLockRangeSq()
    let best: Enemy | null = null
    let bestD = range2
    for (const e of this.em.enemies) {
      if (!e.alive) continue
      const d2 = dist2(this.player.x, this.player.y, e.x, e.y)
      if (d2 < bestD) {
        bestD = d2
        best = e
      }
    }
    if (!best) return false
    const baseAngle = Math.atan2(best.y - this.player.y, best.x - this.player.x)
    const spread = 0.1
    const spd = 520 + sumLv * 15
    const dmg = 5.2 + sumLv * 1.45
    const br = 4 + Math.min(3, this.upgrades.fire_salvo * 0.25)
    let fired = false
    for (let i = 0; i < salvo; i++) {
      if (this.bullets.length >= MAX_BULLETS) break
      const off = salvo > 1 ? (i - (salvo - 1) / 2) * spread : 0
      const ang = baseAngle + off
      const nx = Math.cos(ang)
      const ny = Math.sin(ang)
      this.bullets.push({
        id: this.nextBulletId++,
        x: this.player.x + nx * (this.player.r + 4),
        y: this.player.y + ny * (this.player.r + 4),
        vx: nx * spd,
        vy: ny * spd,
        r: br,
        dmg,
        life: 1.4,
        alive: true,
      })
      fired = true
    }
    return fired
  }

  private ringOrbCount() {
    return Math.min(12, Math.max(0, this.upgrades.ring_count))
  }

  private ringOrbitRadius() {
    const c = this.upgrades.ring_count
    return 44 + Math.max(c, 1) * 4
  }

  private ringOrbRadius() {
    return 3.2
  }

  private ringOrbDamage() {
    const c = this.upgrades.ring_count
    const spin = this.upgrades.ring_spin
    const n = this.ringOrbCount()
    return 2.8 + c * 0.22 + n * 0.35 + spin * 0.42
  }

  private getRingOrbPositions(): { ox: number; oy: number }[] {
    const n = this.ringOrbCount()
    if (n <= 0) return []
    const R = this.ringOrbitRadius()
    const spin = this.upgrades.ring_spin
    const spd = 1.28 + spin * 0.1 + n * 0.035
    const base = this.gameTime * spd
    const px = this.player.x
    const py = this.player.y
    const out: { ox: number; oy: number }[] = []
    for (let i = 0; i < n; i++) {
      const a = base + (i / n) * Math.PI * 2
      out.push({ ox: px + Math.cos(a) * R, oy: py + Math.sin(a) * R })
    }
    return out
  }

  update(dt: number) {
    if (this.gameOver || this.pausedUpgrade || this.rulesFrozen) return

    const step = dt <= 0 ? 1 / 120 : Math.min(0.05, dt)

    this.gameTime += step
    const p = this.player

    if (this.hitFlash > 0) this.hitFlash -= step
    if (this.hitShake > 0) this.hitShake -= step

    let mx = this.moveX
    let my = this.moveY
    if (this.useMouseMove) {
      const tmx = this.mouseWorldX - p.x
      const tmy = this.mouseWorldY - p.y
      const d = len(tmx, tmy)
      if (d > 8) {
        const n = norm(tmx, tmy)
        mx += n.x
        my += n.y
      }
    }
    const ml = len(mx, my)
    if (ml > 1) {
      const n = norm(mx, my)
      mx = n.x
      my = n.y
    }

    const spd = BASE_MOVE * this.moveSpeedMultiplier() * 0.92
    p.x += mx * spd * step
    p.y += my * spd * step
    p.x += this.knockVx * step
    p.y += this.knockVy * step
    const kDecay = Math.pow(0.08, step / 0.05)
    this.knockVx *= kDecay
    this.knockVy *= kDecay

    this.trailAcc += step
    if (ml > 0.12 && this.trailAcc > 0.03) {
      this.trailAcc = 0
      for (let i = 0; i < 2 && this.trails.length < 200; i++) {
        this.trails.push({
          x: p.x + (Math.random() - 0.5) * 6,
          y: p.y + (Math.random() - 0.5) * 6,
          life: 0,
          maxLife: 0.28 + Math.random() * 0.1,
          size: 2.5 + Math.random() * 3.5,
        })
      }
    }

    if (p.invuln > 0) p.invuln -= step

    const halfW = this.w / this.dpr / 2 + 80
    const halfH = this.h / this.dpr / 2 + 80
    const wt = this.worldDifficultyTier()
    this.spawnAcc += this.spawnRatePerSec() * step
    while (this.spawnAcc >= 1) {
      this.spawnAcc -= 1
      const tier = tierRoll(wt)
      const st = tierStats(tier, wt)
      this.em.spawnOutsideView(p.x, p.y, halfW, halfH, 60, st.hp, st.r, st.spd, tier)
    }

    const rateLv = this.upgrades.fire_rate
    // 与旧版单轨「激光等级」的射速公式一致：0.3 - lv*0.017，下限 0.088s
    const interval = Math.max(0.088, 0.3 - rateLv * 0.017)
    this.laserAcc += step
    while (this.laserAcc >= interval) {
      if (!this.tryFireLaser()) break
      this.laserAcc -= interval
    }

    for (const e of this.em.enemies) {
      if (e.ringHitCd > 0) e.ringHitCd -= step
    }

    if (this.ringOrbCount() > 0) {
      const orbs = this.getRingOrbPositions()
      const orbR = this.ringOrbRadius()
      const dmg = this.ringOrbDamage()
      const touch = orbR + 0.5
      for (const e of this.em.enemies) {
        if (!e.alive) continue
        if (e.ringHitCd > 0) continue
        for (const o of orbs) {
          const tr = touch + e.r
          if (dist2(o.ox, o.oy, e.x, e.y) < tr * tr) {
            e.hp -= dmg
            e.ringHitCd = 0.14
            this.pushParticles(o.ox, o.oy, 3, 0.35)
            if (e.hp <= 0) {
              this.killEnemy(e, 2 + Math.floor(wt * 0.6), 3, 5)
            }
            break
          }
        }
      }
    }

    const aggroR2 = AGGRO_RANGE * AGGRO_RANGE
    const viewHalfW = this.w / this.dpr / 2
    const viewHalfH = this.h / this.dpr / 2
    for (const e of this.em.enemies) {
      if (!e.alive) continue
      const d2pe = dist2(p.x, p.y, e.x, e.y)
      const onScreen =
        Math.abs(e.x - p.x) <= viewHalfW + e.r + 4 && Math.abs(e.y - p.y) <= viewHalfH + e.r + 4
      if (!e.committedAggro && (onScreen || d2pe <= aggroR2)) {
        e.committedAggro = true
      }

      if (e.committedAggro) {
        const { x: nx, y: ny } = norm(p.x - e.x, p.y - e.y)
        e.vx = nx * e.baseSpd
        e.vy = ny * e.baseSpd
      } else if (e.probeT > 0) {
        e.probeT -= step
        const { x: nx, y: ny } = norm(p.x - e.x, p.y - e.y)
        const ps = e.baseSpd * PROBE_SPD_MUL
        e.vx = nx * ps
        e.vy = ny * ps
      } else {
        const wob = Math.sin(this.gameTime * 1.55 + e.wanderPhase * 1.3) * 0.4
        const spin = 0.52 + (e.id % 7) * 0.045
        const ang = e.wanderPhase + this.gameTime * spin + wob
        const ws = e.baseSpd * WANDER_SPD_MUL
        e.vx = Math.cos(ang) * ws
        e.vy = Math.sin(ang) * ws
      }
      e.x += (e.vx + e.pullVx) * step
      e.y += (e.vy + e.pullVy) * step
      e.pullVx *= 0.88
      e.pullVy *= 0.88
      if (p.invuln <= 0) {
        const touch = p.r + e.r - 0.5
        if (dist2(p.x, p.y, e.x, e.y) < touch * touch) {
          const dmg = (7 + e.tier * 3) * step * (0.85 + wt * 0.05)
          p.hp -= dmg
          this.hitFlash = Math.max(this.hitFlash, 0.14)
          this.hitShake = Math.max(this.hitShake, 0.12)
          const { x: kx, y: ky } = norm(p.x - e.x, p.y - e.y)
          const kb = 210
          this.knockVx += kx * kb * step
          this.knockVy += ky * kb * step
          if (p.hp <= 0) {
            p.hp = 0
            this.gameOver = true
          }
        }
      }
    }

    for (const b of this.bullets) {
      if (!b.alive) continue
      b.x += b.vx * step
      b.y += b.vy * step
      b.life -= step
      if (b.life <= 0) b.alive = false
    }

    for (const b of this.bullets) {
      if (!b.alive) continue
      for (const e of this.em.enemies) {
        if (!e.alive) continue
        const touch = b.r + e.r
        if (dist2(b.x, b.y, e.x, e.y) < touch * touch) {
          e.hp -= b.dmg
          b.alive = false
          this.pushParticles(b.x, b.y, 5, 0.5)
          if (e.hp <= 0) {
            this.killEnemy(e, 2 + Math.floor(wt * 0.5), 3, 6)
          }
          break
        }
      }
    }

    for (const c of this.crystals) {
      if (!c.alive) continue
      c.vx *= 0.92
      c.vy *= 0.92
      c.x += c.vx * step
      c.y += c.vy * step
      const pr = PICKUP_R + c.r
      if (dist2(p.x, p.y, c.x, c.y) < pr * pr) {
        c.alive = false
        p.xp += c.value
        this.score += 1
        this.tryLevelUp()
      }
    }

    for (const h of this.healthPacks) {
      if (!h.alive) continue
      h.vx *= 0.9
      h.vy *= 0.9
      h.x += h.vx * step
      h.y += h.vy * step
      const hr = PICKUP_R + h.r
      if (dist2(p.x, p.y, h.x, h.y) < hr * hr) {
        h.alive = false
        const heal = Math.min(p.maxHp - p.hp, p.maxHp * 0.07 + 6)
        p.hp += heal
        this.hitFlash = 0
        this.pushParticles(h.x, h.y, 14, 0.6)
      }
    }

    for (let i = this.particles.length - 1; i >= 0; i--) {
      const q = this.particles[i]!
      q.life -= step
      q.x += q.vx * step
      q.y += q.vy * step
      q.vx *= 0.96
      q.vy *= 0.96
      if (q.life <= 0) this.particles.splice(i, 1)
    }

    for (let i = this.trails.length - 1; i >= 0; i--) {
      const t = this.trails[i]!
      t.life += step
      if (t.life >= t.maxLife) this.trails.splice(i, 1)
    }

    for (let i = this.shards.length - 1; i >= 0; i--) {
      const s = this.shards[i]!
      s.life += step
      s.x += s.vx * step
      s.y += s.vy * step
      s.vx *= 0.92
      s.vy *= 0.92
      s.rot += s.vr * step
      if (s.life >= s.maxLife) this.shards.splice(i, 1)
    }

    this.em.removeDead()
    this.bullets = this.bullets.filter((b) => b.alive)
    this.crystals = this.crystals.filter((c) => c.alive)
    this.healthPacks = this.healthPacks.filter((h) => h.alive)
  }

  render(ctx: CanvasRenderingContext2D) {
    const dpr = this.dpr
    const cw = this.w
    const ch = this.h
    const viewW = cw / dpr
    const viewH = ch / dpr
    const px = this.player.x
    const py = this.player.y

    let sx = 0
    let sy = 0
    if (this.hitShake > 0) {
      const k = this.hitShake / 0.12
      sx = (Math.random() - 0.5) * 6 * k
      sy = (Math.random() - 0.5) * 6 * k
    }

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    const sky = ctx.createLinearGradient(0, 0, 0, viewH)
    sky.addColorStop(0, "#1a1732")
    sky.addColorStop(0.55, "#121028")
    sky.addColorStop(1, "#0a0816")
    ctx.fillStyle = sky
    ctx.fillRect(0, 0, viewW, viewH)

    const gx = viewW / 2 - px + sx
    const gy = viewH / 2 - py + sy

    ctx.save()
    ctx.translate(gx, gy)

    ctx.strokeStyle = "rgba(150,110,220,0.085)"
    ctx.lineWidth = 1
    const grid = 64
    const startX = Math.floor((px - viewW / 2) / grid) * grid
    const startY = Math.floor((py - viewH / 2) / grid) * grid
    for (let x = startX; x < px + viewW / 2 + grid; x += grid) {
      ctx.beginPath()
      ctx.moveTo(x, py - viewH)
      ctx.lineTo(x, py + viewH)
      ctx.stroke()
    }
    for (let y = startY; y < py + viewH / 2 + grid; y += grid) {
      ctx.beginPath()
      ctx.moveTo(px - viewW, y)
      ctx.lineTo(px + viewW, y)
      ctx.stroke()
    }

    for (const c of this.crystals) {
      if (!c.alive) continue
      const g = ctx.createRadialGradient(c.x, c.y, 0, c.x, c.y, c.r * 3)
      g.addColorStop(0, "rgba(255,180,235,0.95)")
      g.addColorStop(0.45, "rgba(196,120,255,0.55)")
      g.addColorStop(1, "rgba(120,60,200,0)")
      ctx.fillStyle = g
      ctx.beginPath()
      ctx.arc(c.x, c.y, c.r * 2.2, 0, Math.PI * 2)
      ctx.fill()
    }

    for (const h of this.healthPacks) {
      if (!h.alive) continue
      ctx.shadowColor = "rgba(110,255,200,0.55)"
      ctx.shadowBlur = 14
      const g = ctx.createRadialGradient(h.x, h.y, 0, h.x, h.y, h.r * 2.4)
      g.addColorStop(0, "rgba(200,255,240,0.95)")
      g.addColorStop(0.4, "rgba(80,220,180,0.45)")
      g.addColorStop(1, "rgba(40,120,100,0)")
      ctx.fillStyle = g
      ctx.beginPath()
      ctx.arc(h.x, h.y, h.r * 1.35, 0, Math.PI * 2)
      ctx.fill()
      ctx.shadowBlur = 0
      ctx.strokeStyle = "rgba(255,255,255,0.65)"
      ctx.lineWidth = 1.2
      ctx.beginPath()
      ctx.arc(h.x, h.y, h.r * 1.35, 0, Math.PI * 2)
      ctx.stroke()
      const cr = h.r * 0.55
      ctx.strokeStyle = "rgba(255,255,255,0.9)"
      ctx.lineWidth = 1.8
      ctx.lineCap = "round"
      ctx.beginPath()
      ctx.moveTo(h.x - cr, h.y)
      ctx.lineTo(h.x + cr, h.y)
      ctx.moveTo(h.x, h.y - cr)
      ctx.lineTo(h.x, h.y + cr)
      ctx.stroke()
    }

    for (const e of this.em.enemies) {
      if (!e.alive) continue
      if (e.tier === 1) {
        const pulse = 0.5 + 0.5 * Math.sin(this.gameTime * 4.2 + e.id * 0.7)
        ctx.strokeStyle = `rgba(255,160,130,${0.35 + pulse * 0.28})`
        ctx.lineWidth = 1.4
        ctx.setLineDash([4, 3])
        ctx.beginPath()
        ctx.arc(e.x, e.y, e.r + 6 + pulse * 2.5, 0, Math.PI * 2)
        ctx.stroke()
        ctx.setLineDash([])
        ctx.strokeStyle = `rgba(255,210,180,${0.22 + pulse * 0.18})`
        ctx.lineWidth = 2.2
        ctx.beginPath()
        ctx.arc(e.x, e.y, e.r + 3.5, 0, Math.PI * 2)
        ctx.stroke()
      }
      if (e.tier === 1) {
        ctx.fillStyle = "rgba(255,115,95,0.94)"
        ctx.strokeStyle = "rgba(255,210,185,0.82)"
      } else if (e.tier === 2) {
        ctx.fillStyle = "rgba(195,105,255,0.95)"
        ctx.strokeStyle = "rgba(235,195,255,0.78)"
      } else {
        ctx.fillStyle = "rgba(255,95,195,0.96)"
        ctx.strokeStyle = "rgba(255,215,245,0.88)"
      }
      ctx.lineWidth = e.tier === 3 ? 1.6 : 1.2
      ctx.beginPath()
      ctx.arc(e.x, e.y, e.r, 0, Math.PI * 2)
      ctx.fill()
      ctx.stroke()
    }

    for (const b of this.bullets) {
      if (!b.alive) continue
      ctx.shadowColor = "rgba(255,120,200,0.9)"
      ctx.shadowBlur = 12
      const g = ctx.createRadialGradient(b.x, b.y, 0, b.x, b.y, b.r * 2.5)
      g.addColorStop(0, "#fff0fb")
      g.addColorStop(0.35, "#ff6eb4")
      g.addColorStop(1, "rgba(180,60,200,0)")
      ctx.fillStyle = g
      ctx.beginPath()
      ctx.arc(b.x, b.y, b.r * 1.8, 0, Math.PI * 2)
      ctx.fill()
      ctx.shadowBlur = 0
    }

    if (this.ringOrbCount() > 0 && !this.pausedUpgrade && !this.gameOver) {
      const orbs = this.getRingOrbPositions()
      const orbR = this.ringOrbRadius()
      for (const o of orbs) {
        ctx.shadowColor = "rgba(255,255,255,0.75)"
        ctx.shadowBlur = 10
        const g = ctx.createRadialGradient(o.ox, o.oy, 0, o.ox, o.oy, orbR * 2.8)
        g.addColorStop(0, "rgba(255,255,255,0.95)")
        g.addColorStop(0.35, "rgba(240,248,255,0.45)")
        g.addColorStop(1, "rgba(200,220,255,0)")
        ctx.fillStyle = g
        ctx.beginPath()
        ctx.arc(o.ox, o.oy, orbR, 0, Math.PI * 2)
        ctx.fill()
        ctx.shadowBlur = 0
      }
    }

    for (const t of this.trails) {
      const a = 1 - t.life / t.maxLife
      const s = t.size * (0.4 + 0.6 * (1 - a))
      const g = ctx.createRadialGradient(t.x, t.y, 0, t.x, t.y, s)
      g.addColorStop(0, `rgba(255,200,245,${0.4 * (1 - a)})`)
      g.addColorStop(0.55, `rgba(200,150,255,${0.22 * (1 - a)})`)
      g.addColorStop(1, "rgba(120,80,200,0)")
      ctx.fillStyle = g
      ctx.beginPath()
      ctx.arc(t.x, t.y, s, 0, Math.PI * 2)
      ctx.fill()
    }

    for (const s of this.shards) {
      const a = 1 - s.life / s.maxLife
      ctx.save()
      ctx.translate(s.x, s.y)
      ctx.rotate(s.rot)
      ctx.globalAlpha = 0.15 + (1 - a) * 0.85
      let fill = "rgba(255,95,195,0.92)"
      if (s.tier === 1) fill = "rgba(255,115,95,0.9)"
      if (s.tier === 2) fill = "rgba(195,105,255,0.92)"
      if (s.tier === 3) fill = "rgba(255,95,195,0.95)"
      ctx.fillStyle = fill
      ctx.strokeStyle = "rgba(255,255,255,0.35)"
      ctx.lineWidth = 0.6
      ctx.beginPath()
      ctx.moveTo(s.size, 0)
      ctx.lineTo(-s.size * 0.5, s.size * 0.75)
      ctx.lineTo(-s.size * 0.5, -s.size * 0.75)
      ctx.closePath()
      ctx.fill()
      ctx.stroke()
      ctx.restore()
    }
    ctx.globalAlpha = 1

    const pr = this.player.r
    if (this.hitFlash > 0) {
      const hf = this.hitFlash / 0.14
      ctx.strokeStyle = `rgba(255,255,255,${0.35 + hf * 0.45})`
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.arc(px, py, pr + 6 + (1 - hf) * 4, 0, Math.PI * 2)
      ctx.stroke()
    }

    ctx.shadowColor = "rgba(255,255,255,0.55)"
    ctx.shadowBlur = 18
    const pg = ctx.createRadialGradient(px, py, 0, px, py, pr * 2.2)
    pg.addColorStop(0, "rgba(255,255,255,0.98)")
    pg.addColorStop(0.35, "rgba(245,248,255,0.55)")
    pg.addColorStop(0.7, "rgba(220,230,255,0.2)")
    pg.addColorStop(1, "rgba(180,200,255,0)")
    ctx.fillStyle = pg
    ctx.beginPath()
    ctx.arc(px, py, pr, 0, Math.PI * 2)
    ctx.fill()
    ctx.shadowBlur = 0

    ctx.fillStyle = "rgba(255,255,255,0.92)"
    ctx.beginPath()
    ctx.arc(px, py, pr * 0.55, 0, Math.PI * 2)
    ctx.fill()

    for (const q of this.particles) {
      const a = Math.max(0, q.life / 0.55)
      let col = "rgba(255,140,220,"
      if (q.kind === "violet") col = "rgba(190,120,255,"
      if (q.kind === "white") col = "rgba(255,250,255,"
      ctx.fillStyle = `${col}${0.35 + a * 0.5})`
      ctx.beginPath()
      ctx.arc(q.x, q.y, q.size * (0.5 + a * 0.5), 0, Math.PI * 2)
      ctx.fill()
    }

    ctx.restore()
  }
}
