import { Application } from "pixi.js"

import { HEIGHT, WIDTH } from "../constants"
import { GameEngine } from "../engine/GameEngine"
import { bakedTextureCount } from "./artAssets"
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
    // 全屏覆盖层（闪白/变暗/星级）钉在 stage 顶层，不随屏震平移
    app.stage.addChild(battle.overlay)

    app.ticker.add((ticker) => {
      const dtMs = ticker.deltaMS
      // 取证冻结：画布保留最后一帧（截图「特效瞬间」用；不影响引擎契约）
      if (battle.frozen) return
      // hit-stop（命中停顿）：重弹/爆裂大命中后 50ms 冻结世界时钟（art bible §5）。
      // 引擎 tick 与渲染 sync 同时跳过 = 物理与视觉一起停，引擎零改动。
      if (battle.consumeHitStop(dtMs)) return
      starField.update(dtMs / 1000)
      engine.update(dtMs)
      battle.sync(dtMs / 1000)
    })

    // 只读调试钩子（与 __staEngine 同性质）：截图取证用的时钟冻结开关 + 性能读数
    if (typeof window !== "undefined") {
      ;(window as unknown as {
        __staFx?: {
          freeze: () => void
          unfreeze: () => void
          stats: () => { particles: number; bakedTextures: number; frozen: boolean }
        }
      }).__staFx = {
        freeze: () => {
          battle.frozen = true
        },
        unfreeze: () => {
          battle.frozen = false
        },
        stats: () => ({
          particles: battle.particleCount,
          bakedTextures: bakedTextureCount(),
          frozen: battle.frozen,
        }),
      }
    }
  }

  destroy(): void {
    if (typeof window !== "undefined") {
      // 只摘自己的钩子：StrictMode 双挂载下旧实例的 destroy 可能晚于新实例 mount 到达，
      // 无条件 delete 会把新实例刚挂上的 __staEngine 一并抹掉（自动化探针就瞎了）。
      const w = window as unknown as { __staEngine?: GameEngine }
      if (w.__staEngine === this.engine) delete w.__staEngine
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
