import type { NebulaEvent } from "../nebulaEngine"

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

  /** 引擎事件 → 音效（纯反馈，不改模拟） */
  handleEvent(e: NebulaEvent): void {
    if (!this.ctx) return
    switch (e.type) {
      case "shoot":
        this.shoot()
        break
      case "damage":
        this.hit()
        break
      case "enemy-killed":
        this.explode(e.tier)
        break
      case "level-up":
        this.levelUp()
        break
      case "player-healed":
        this.pickup()
        break
      case "player-died":
        this.died()
        break
    }
  }
}

export const nebulaSfx = new NebulaSfx()
