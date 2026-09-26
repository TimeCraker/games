import { Application } from "pixi.js"

import { NebulaEngine } from "../nebulaEngine"
import { NebulaBackground } from "./NebulaBackground"
import { NebulaScene } from "./NebulaScene"

/**
 * Pixi 渲染主机（对齐 StaPixiApp 模式）。
 * 常驻 Application（挂载/卸载不抢 WebGL context）；tick 驱动 背景 → 引擎模拟 → 场景同步。
 * 模拟(stim)仍由 NebulaEngine 持有，主类别名 .engine 供 React 输入层读取。
 */
export class NebulaPixiHost {
  readonly engine = new NebulaEngine()

  private app: Application | null = null
  private bg = new NebulaBackground()
  private scene = new NebulaScene(this.engine)
  private ro: ResizeObserver | null = null

  async mount(container: HTMLElement): Promise<void> {
    const w = Math.max(280, Math.floor(container.clientWidth || 800))
    const h = Math.max(360, Math.floor(container.clientHeight || 600))

    const app = new Application()
    await app.init({
      width: w,
      height: h,
      antialias: true,
      background: 0x050514,
      resolution: Math.min(2, typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1),
      autoDensity: true,
      preference: "webgl",
      powerPreference: "high-performance",
    })

    const canvas = app.canvas as HTMLCanvasElement
    canvas.style.display = "block"
    canvas.style.width = "100%"
    canvas.style.height = "100%"
    canvas.style.touchAction = "none"
    container.appendChild(canvas)
    this.app = app

    // Pixi v8 默认 AccessibilitySystem 会注入 1×1 隐藏可聚焦按钮，是 Tab 环隐形陷阱：移除
    try {
      ;(app as unknown as { accessibility?: { destroy?: () => void } }).accessibility?.destroy?.()
      container.querySelectorAll<HTMLElement>('[title*="enable accessibility"], [aria-label*="enable accessibility"]').forEach((n) => n.remove())
    } catch {
      /* ignore */
    }

    this.engine.w = w
    this.engine.h = h
    this.engine.dpr = 1
    this.scene.viewW = w
    this.scene.viewH = h
    this.bg.setSize(w, h)

    app.stage.addChild(this.bg.container)
    app.stage.addChild(this.scene.stage)

    this.ro = new ResizeObserver(() => {
      const cw = Math.max(280, Math.floor(container.clientWidth || w))
      const ch = Math.max(360, Math.floor(container.clientHeight || h))
      this.app?.renderer.resize(cw, ch)
      this.engine.w = cw
      this.engine.h = ch
      this.engine.dpr = 1
      this.scene.viewW = cw
      this.scene.viewH = ch
      this.bg.setSize(cw, ch)
    })
    this.ro.observe(container)

    app.ticker.add((ticker) => {
      const dt = Math.min(0.05, Math.max(1 / 240, ticker.deltaMS / 1000))
      this.bg.update(dt)
      this.engine.update(dt)
      this.scene.sync(dt)
    })
  }

  destroy(): void {
    this.ro?.disconnect()
    this.ro = null
    if (this.app) {
      this.app.destroy(true, { children: true, texture: true })
      this.app = null
    }
  }
}
