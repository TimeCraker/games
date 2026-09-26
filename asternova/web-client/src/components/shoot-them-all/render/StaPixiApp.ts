import { Application } from "pixi.js"

import { HEIGHT, WIDTH } from "../constants"
import { GameEngine } from "../engine/GameEngine"
import { BattleScene } from "./BattleScene"
import { StarFieldBg } from "./StarFieldBg"

/**
 * Pixi 渲染主机（Stage Spec §8.1/§8.7）。
 * 常驻 Application（场景切换不 destroy app 以避免 WebGL context 丢失）。
 * 物理由 GameEngine（matter）持有；本类 tick 引擎 + 同步渲染。
 *
 * 关键：每个 Application 自带 canvas（挂到容器），规避 React StrictMode 双挂载抢同一 WebGL context。
 */
export class StaPixiApp {
  private app: Application | null = null
  private starField: StarFieldBg | null = null
  private battle: BattleScene | null = null
  private engine: GameEngine | null = null

  /** 供输入层（React）访问引擎。挂载前为 null。 */
  get gameEngine(): GameEngine | null {
    return this.engine
  }

  async mount(container: HTMLElement): Promise<void> {
    const app = new Application()
    await app.init({
      width: WIDTH,
      height: HEIGHT,
      antialias: true,
      background: 0x050608,
      resolution: Math.min(typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1, 2),
      autoDensity: true,
      preference: "webgl",
      powerPreference: "high-performance",
    })

    const canvas = app.canvas as HTMLCanvasElement
    canvas.style.display = "block"
    canvas.style.width = "100%"
    canvas.style.height = "100%"
    container.appendChild(canvas)
    this.app = app

    // Pixi v8 默认开启 AccessibilitySystem 并注入一个 1×1 的隐藏可聚焦按钮
    // （aria-label="select to enable accessibility for this content"）。
    // 本作没有任何 accessible 语义对象，它只是键盘 Tab 的隐形陷阱：移除以保持 Tab 环干净。
    try {
      ;(app as unknown as { accessibility?: { destroy?: () => void } }).accessibility?.destroy?.()
      container.querySelectorAll<HTMLElement>('[title*="enable accessibility"], [aria-label*="enable accessibility"]').forEach((n) => n.remove())
    } catch {
      /* ignore */
    }

    const starField = new StarFieldBg()
    this.starField = starField
    app.stage.addChild(starField.container)

    const engine = new GameEngine()
    this.engine = engine

    // 只读调试钩子：本作的内部状态（球速 / 相位 / 物理是否真的在步进）无法从 DOM 观察，
    // 而自动化探针又必须能断言这些量（历史上正是靠它才发现「球卡在发射位、物理未推进」）。
    // 仅挂引用，不改任何游戏逻辑；__ 前缀避免与业务命名冲突。
    if (typeof window !== "undefined") {
      ;(window as unknown as { __staEngine?: GameEngine }).__staEngine = engine
    }
    const battle = new BattleScene(engine)
    this.battle = battle
    engine.onEvent = battle.handleEngineEvent
    app.stage.addChild(battle.container)

    app.ticker.add((ticker) => {
      starField.update(ticker.deltaMS / 1000)
      engine.update(ticker.deltaMS)
      battle.sync(ticker.deltaMS / 1000)
    })
  }

  destroy(): void {
    if (typeof window !== "undefined") {
      delete (window as unknown as { __staEngine?: GameEngine }).__staEngine
    }
    this.engine?.destroy()
    this.engine = null
    this.battle = null
    this.starField = null
    if (this.app) {
      this.app.destroy(true, { children: true, texture: true })
      this.app = null
    }
  }
}
