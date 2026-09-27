import type { EnemyKind, SimEvent } from "../sim/types"

/** 敌方档位 → 爆炸音色的档位编号 */
const KILL_TIER: Record<EnemyKind, number> = { scout: 1, drone: 2, heavy: 3, boss: 4 }

const STORAGE_VOLUME = "nebula-sfx-volume"

/**
 * WebAudio 合成音效（零素材）：射击/命中/爆炸/升级/拾取/受击。
 * 单例（模块导出 nebulaSfx）；音量 localStorage 持久化。
 * 首手势后 ensure() 恢复 AudioContext（autoplay 合规，恢复前静默）。
 */
export class NebulaSfx {
  private ctx: AudioContext | null = null
  private master: GainNode | null = null
  private _volume = 0.6
  private lastPlay: Record<string, number> = {}

  constructor() {
    try {
      const raw = localStorage.getItem(STORAGE_VOLUME)
      if (raw != null) {
        const n = Number(raw)
        if (Number.isFinite(n)) this._volume = Math.max(0, Math.min(1, n))
      }
    } catch {
      /* ignore */
    }
  }

  get volume(): number {
    return this._volume
  }

  set volume(v: number) {
    this._volume = Math.max(0, Math.min(1, v))
    if (this.master) this.master.gain.value = this._volume
    try {
      localStorage.setItem(STORAGE_VOLUME, String(this._volume))
    } catch {
      /* ignore */
    }
  }

  get muted(): boolean {
    return this._volume <= 0.001
  }

  /** 首次用户手势时调用：创建并恢复 AudioContext（autoplay 政策） */
  ensure(): void {
    if (!this.ctx) {
      try {
        const AC = window.AudioContext
        if (!AC) return
        this.ctx = new AC()
        this.master = this.ctx.createGain()
        this.master.gain.value = this._volume
        this.master.connect(this.ctx.destination)
      } catch {
        return
      }
    }
    if (this.ctx.state === "suspended") void this.ctx.resume().catch(() => {})
  }

  private throttled(key: string, ms: number): boolean {
    const now = performance.now()
    if (now - (this.lastPlay[key] ?? 0) < ms) return true
    this.lastPlay[key] = now
    return false
  }

  private tone(freq: number, dur: number, type: OscillatorType, vol: number, slideTo?: number): void {
    if (!this.ctx || !this.master || this.muted) return
    const t = this.ctx.currentTime
    const osc = this.ctx.createOscillator()
    const g = this.ctx.createGain()
    osc.type = type
    osc.frequency.setValueAtTime(freq, t)
    if (slideTo) osc.frequency.exponentialRampToValueAtTime(Math.max(1, slideTo), t + dur)
    g.gain.setValueAtTime(0.0001, t)
    g.gain.exponentialRampToValueAtTime(vol, t + 0.006)
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur)
    osc.connect(g)
    g.connect(this.master)
    osc.start(t)
    osc.stop(t + dur + 0.03)
  }

  private noise(dur: number, vol: number, cutoff: number): void {
    if (!this.ctx || !this.master || this.muted) return
    const t = this.ctx.currentTime
    const len = Math.max(1, Math.floor(this.ctx.sampleRate * dur))
    const buf = this.ctx.createBuffer(1, len, this.ctx.sampleRate)
    const data = buf.getChannelData(0)
    for (let i = 0; i < len; i++) data[i] = Math.random() * 2 - 1
    const src = this.ctx.createBufferSource()
    src.buffer = buf
    const filter = this.ctx.createBiquadFilter()
    filter.type = "lowpass"
    filter.frequency.value = cutoff
    const g = this.ctx.createGain()
    g.gain.setValueAtTime(vol, t)
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur)
    src.connect(filter)
    filter.connect(g)
    g.connect(this.master)
    src.start(t)
  }

  private shoot(): void {
    if (this.throttled("shoot", 70)) return
    this.tone(900, 0.07, "square", 0.09, 180)
  }

  private hit(): void {
    if (this.throttled("hit", 40)) return
    this.noise(0.05, 0.16, 2000)
  }

  private explode(tier: number): void {
    this.noise(0.32, 0.5, 900 - tier * 120)
    this.tone(130 + tier * 40, 0.28, "triangle", 0.28, 40)
  }

  private levelUp(): void {
    const notes = [523, 659, 784, 1047]
    notes.forEach((f, i) => window.setTimeout(() => this.tone(f, 0.18, "triangle", 0.2), i * 70))
  }

  private pickup(): void {
    this.tone(1200, 0.08, "sine", 0.16, 1900)
  }

  private hurt(): void {
    this.tone(170, 0.22, "sawtooth", 0.24, 60)
    this.noise(0.18, 0.22, 700)
  }

  private died(): void {
    this.noise(0.6, 0.55, 500)
    this.tone(80, 0.6, "triangle", 0.36, 28)
  }

  /** 三合一升星：本作唯一的高光时刻，给一段上行琶音 + 金属噪 */
  private merge(stars: number): void {
    const base = [660, 880, 1100, 1320]
    const n = Math.min(4, 1 + Math.floor(stars / 2))
    for (let i = 0; i < n; i++) {
      window.setTimeout(() => this.tone(base[i], 0.16, "triangle", 0.20, base[i] * 1.5), i * 55)
    }
    this.noise(0.22, 0.24, 4200)
  }

  /** E 技：短促上扬的气流 */
  private eskill(): void {
    this.noise(0.16, 0.18, 1600)
    this.tone(240, 0.2, "sine", 0.14, 900)
  }

  /** 波次推进 / Boss 登场 */
  private bossWave(): void {
    this.tone(110, 0.7, "sawtooth", 0.22, 55)
    this.noise(0.5, 0.3, 600)
  }

  /** 模拟事件 → 音效（纯反馈，绝不回流进模拟） */
  handleEvent(e: SimEvent): void {
    if (!this.ctx) return
    switch (e.type) {
      case "shoot": this.shoot(); break
      case "hit": this.hit(); break
      case "kill":
        if (e.kind === "boss") { this.explode(4); this.bossWave() } else this.explode(KILL_TIER[e.kind])
        break
      case "levelup": this.levelUp(); break
      case "pickup":
        if (e.kind === "health") this.pickup()
        else if (e.kind === "weapon") this.merge(1)
        break
      case "merge": this.merge(e.stars); break
      case "hurt": this.hurt(); break
      case "death": this.died(); break
      case "eskill": this.eskill(); break
      case "wave": if (e.wave % 5 === 0) this.bossWave(); break
    }
  }
}

export const nebulaSfx = new NebulaSfx()
