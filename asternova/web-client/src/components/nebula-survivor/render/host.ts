import { Application } from "pixi.js"

import { FIXED_DT, MAX_CATCHUP_STEPS, Sim, type SimOptions } from "../sim/Sim"
import { nebulaSfx } from "./NebulaSfx"
import { NebulaScene } from "./scene"

/** 交给 React HUD 的只读读数（每个 UI tick 一份，不暴露模拟内部对象） */
export type UiSnapshot = {
  hp: number; maxHp: number
  level: number; xp: number; xpToNext: number
  wave: number; kills: number; score: number; coins: number
  time: number; dps: number
  weapons: { id: string; stars: number; mergeCount: number }[]
  eskill: string; eskillCd: number; eskillReady: boolean
  shopOpen: boolean; gameOver: boolean; bossAlive: boolean
  flash: number; hurt: number
  /** 雷达光点：方位角（弧度）+ 归一化距离（0..1）+ 档位 */
  radar: { a: number; d: number; kind: string }[]
}

export type NebulaHostOptions = SimOptions & { onUi?: (s: UiSnapshot) => void }

/**
 * Pixi 宿主 + **固定步长累加器**。
 *
 * 关键契约（白皮书 §11.1）：模拟永远以 1/60 秒推进，渲染帧率与之解耦。
 * 一帧内最多补 MAX_CATCHUP_STEPS 步，防止切后台回来炸帧。
 * 命中顿感（hitStop）冻结模拟但继续推进渲染，产生打击顿感。
 */
export class NebulaHost {
  readonly sim: Sim
  onUi: ((s: UiSnapshot) => void) | null

  private app: Application | null = null
  private scene: NebulaScene | null = null
  private ro: ResizeObserver | null = null
  private acc = 0
  private uiAcc = 0

  constructor(opts: NebulaHostOptions) {
    this.sim = new Sim(opts)
    this.onUi = opts.onUi ?? null
  }

  async mount(container: HTMLElement): Promise<void> {
    const w = Math.max(320, Math.floor(container.clientWidth || 960))
    const h = Math.max(320, Math.floor(container.clientHeight || 540))

    const app = new Application()
    await app.init({
      width: w, height: h,
      antialias: true,
      background: 0x050608,
      resolution: Math.min(2, typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1),
      autoDensity: true,
      preference: "webgl",
      powerPreference: "high-performance",
    })
    this.app = app

    const canvas = app.canvas as HTMLCanvasElement
    canvas.style.display = "block"
    canvas.style.width = "100%"
    canvas.style.height = "100%"
    canvas.style.touchAction = "none"
    container.appendChild(canvas)

    const scene = new NebulaScene(app.renderer)
    scene.init(this.sim)
    scene.setSize(w, h)
    app.stage.addChild(scene.stage)
    this.scene = scene

    this.sim.onEvent = (e) => {
      scene.handleEvent(e)
      nebulaSfx.handleEvent(e)
    }

    this.ro = new ResizeObserver(() => {
      const cw = Math.max(320, Math.floor(container.clientWidth || w))
      const ch = Math.max(320, Math.floor(container.clientHeight || h))
      app.renderer.resize(cw, ch)
      scene.setSize(cw, ch)
    })
    this.ro.observe(container)

    app.ticker.add((ticker) => {
      const dt = Math.min(0.25, Math.max(1 / 240, ticker.deltaMS / 1000))
      const sim = this.sim
      if (scene.hitStop > 0) {
        scene.hitStop = Math.max(0, scene.hitStop - dt)
      } else {
        this.acc += dt
        let steps = 0
        while (this.acc >= FIXED_DT && steps < MAX_CATCHUP_STEPS) {
          sim.step()
          this.acc -= FIXED_DT
          steps++
        }
        if (this.acc > FIXED_DT * MAX_CATCHUP_STEPS) this.acc = 0
      }
      sim.tickDps(dt)
      scene.sync(sim, dt)

      this.uiAcc += dt
      if (this.uiAcc >= 0.1) {
        this.uiAcc = 0
        this.onUi?.(this.snapshot())
      }
    })
  }

  snapshot(): UiSnapshot {
    const s = this.sim
    return {
      hp: Math.max(0, Math.round(s.player.hp)), maxHp: Math.round(s.player.maxHp),
      level: s.level, xp: Math.floor(s.xp), xpToNext: s.xpToNext,
      wave: s.wave, kills: s.kills, score: s.score, coins: s.coins,
      time: s.time, dps: Math.round(s.dps),
      weapons: s.weapons.map((w) => ({ id: w.id, stars: w.stars, mergeCount: w.mergeCount })),
      eskill: s.eskill, eskillCd: s.eskillCd,
      eskillReady: s.eskillCd <= 0,
      shopOpen: s.shopOpen, gameOver: s.gameOver, bossAlive: s.bossAlive,
      flash: this.scene?.screenFlash ?? 0,
      hurt: this.scene?.hurtAmount ?? 0,
      radar: this.radar(),
    }
  }

  /** 雷达：取最近的 10 个敌人，换算成「方位角 + 归一化距离」交给 HUD */
  private radar(): { a: number; d: number; kind: string }[] {
    const s = this.sim
    const p = s.player
    const R = 900
    const out: { a: number; d: number; kind: string }[] = []
    for (const e of s.enemies) {
      const dx = e.x - p.x, dy = e.y - p.y
      const dist = Math.hypot(dx, dy)
      if (dist > R) continue
      out.push({ a: Math.atan2(dy, dx), d: Math.min(1, dist / R), kind: e.kind })
      if (out.length >= 10) break
    }
    return out
  }

  setMove(x: number, y: number): void { this.sim.setMove(x, y) }
  useESkill(): void { this.sim.triggerESkill() }

  destroy(): void {
    this.ro?.disconnect()
    this.ro = null
    this.sim.onEvent = null
    this.scene?.destroy()
    this.scene = null
    if (this.app) { this.app.destroy(true, { children: true, texture: true }); this.app = null }
  }
}
