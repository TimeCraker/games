import { Application } from "pixi.js"

import { HEIGHT, WIDTH } from "../constants"
import { StarFieldBg } from "./StarFieldBg"

/**
 * Pixi 渲染主机（Stage Spec §8.1/§8.7）。
 * 常驻 Application（全生命周期不销毁，场景切换不 destroy app 以避免 WebGL context 丢失）。
 * 物理由 engine/ 的 GameEngine 持有 matter；本类只渲染。
 *
 * M1 阶段：仅承载 StarFieldBg，验证 Pixi+React 桥与画布缩放。
 * 后续：注册 EntityRegistry 驱动的 sprite 同步、ParticleSystem、后期栈。
 */
export class StaPixiApp {
  private app: Application | null = null
  private starField: StarFieldBg | null = null

  get ready(): boolean {
    return this.app !== null
  }

  /**
   * 创建自带 canvas 的 Application 并挂入容器。
   * 关键：让每个 Application 拥有自己的 canvas，而非共享 React 传入的 <canvas>。
   * 否则 React StrictMode（Next dev 默认开启）双挂载 effect 时，两个 init() 抢同一
   * canvas 的 WebGL context → "context may be lost" + shader 编译失败（已实测）。
   */
  async mount(container: HTMLElement): Promise<void> {
    const app = new Application()
    await app.init({
      width: WIDTH,
      height: HEIGHT,
      antialias: true,
      background: 0x05060f,
      // 上限 2 维持移动端性能（Stage Spec §8.9 性能预算）
      resolution: Math.min(typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1, 2),
      autoDensity: true,
      preference: "webgl",
      powerPreference: "high-performance",
    })

    // Pixi 自有 canvas 填满容器（容器即 720×1280 舞台）
    const canvas = app.canvas as HTMLCanvasElement
    canvas.style.display = "block"
    canvas.style.width = "100%"
    canvas.style.height = "100%"
    container.appendChild(canvas)
    this.app = app

    const starField = new StarFieldBg()
    this.starField = starField
    app.stage.addChild(starField.container)

    app.ticker.add((ticker) => {
      starField.update(ticker.deltaMS / 1000)
    })
  }

  destroy(): void {
    if (this.app) {
      // removeView=true 移除自挂载的 canvas；children/texture 清理子资源
      this.app.destroy(true, { children: true, texture: true })
      this.app = null
    }
    this.starField = null
  }
}
