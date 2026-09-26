import { Container, Text } from "pixi.js"

interface FloatNum {
  text: Text
  x: number
  y: number
  vy: number
  life: number
  maxLife: number
  active: boolean
}

/**
 * 伤害飘字（对象池复用，零每帧分配）。
 * 上浮 + 淡出 + 弹出缩放；全局数量上限 + 最小间隔节流，避免刷屏。
 */
export class DamageNumbers {
  readonly container = new Container()
  private pool: FloatNum[] = []
  private activeCount = 0
  private lastSpawnAt = -1
  private readonly maxActive = 32
  private readonly minInterval = 0.025

  constructor() {
    this.container.eventMode = "none"
  }

  spawn(x: number, y: number, amount: number, now: number): void {
    if (this.activeCount >= this.maxActive) return
    if (now - this.lastSpawnAt < this.minInterval) return
    this.lastSpawnAt = now

    let f = this.pool.find((q) => !q.active)
    if (!f) {
      const text = new Text({
        text: "",
        style: {
          fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif",
          fontSize: 15,
          fontWeight: "700",
          fill: 0xf4f7ff,
          stroke: { color: 0x0a0a18, width: 4 },
          align: "center",
        },
      })
      text.anchor.set(0.5)
      this.container.addChild(text)
      f = { text, x: 0, y: 0, vy: -40, life: 0, maxLife: 0.7, active: false }
      this.pool.push(f)
    }

    f.text.text = String(Math.round(amount))
    f.x = x + (Math.random() - 0.5) * 10
    f.y = y
    f.vy = -44 - Math.random() * 22
    f.maxLife = 0.55 + Math.random() * 0.25
    f.life = 0
    f.text.visible = true
    f.text.alpha = 1
    f.text.scale.set(1.15)
    f.active = true
    this.activeCount++
  }

  update(dt: number): void {
    if (this.activeCount === 0) return
    for (const f of this.pool) {
      if (!f.active) continue
      f.life += dt
      if (f.life >= f.maxLife) {
        f.active = false
        f.text.visible = false
        this.activeCount--
        continue
      }
      f.y += f.vy * dt
      f.text.position.set(f.x, f.y)
      const p = f.life / f.maxLife
      f.text.alpha = p < 0.65 ? 1 : 1 - (p - 0.65) / 0.35
      const pop = p < 0.12 ? 1.15 - (0.12 - p) * 1.4 : 1
      f.text.scale.set(pop)
    }
  }

  destroy(): void {
    this.container.destroy({ children: true })
  }
}
