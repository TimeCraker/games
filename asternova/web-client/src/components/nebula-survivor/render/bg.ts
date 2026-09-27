import { Container, Sprite, TilingSprite } from "pixi.js"

import { planetTexture, radialGlow, starTile } from "./textures"

/**
 * 底板层（对齐 art/ui/nebula-survivor/target-v1.html 的三层结构）：
 *   sky    屏幕空间渐变（不随相机）
 *   nebula 世界空间星云（视差 0.18，琥珀为主 + 苔绿极小面积点缀）
 *   planet 远景行星（视差 0.10，带大气辉光与受光轮廓）
 *   stars  四层星空（视差 0.25/0.42/0.62/0.85，层间差 = 纵深）
 * 全部程序化贴图，零位图依赖。
 */
export class NebulaBackground {
  readonly container = new Container()
  private sky = new Container()
  private world = new Container()
  private nebula = new Container()
  private planetSprite: Sprite | null = null
  private stars: TilingSprite[] = []
  private parallax = [0.25, 0.42, 0.62, 0.85]
  private viewW = 800
  private viewH = 600
  private skySprite: Sprite

  constructor() {
    const sky = new Sprite(radialGlow("11,13,18", 64))
    sky.anchor.set(0.5)
    this.skySprite = sky
    this.sky.addChild(sky)
    this.container.addChild(this.sky)

    const clouds: [string, number, number, number, number][] = [
      ["216,163,60", -520, -360, 1500, 0.15],
      ["216,163,60", 620, 420, 1250, 0.13],
      ["216,163,60", 120, -600, 1000, 0.11],
      ["156,184,106", 760, -140, 760, 0.07],
      ["156,184,106", -820, 520, 640, 0.06],
    ]
    for (const [rgb, x, y, r, a] of clouds) {
      const s = new Sprite(radialGlow(rgb))
      s.anchor.set(0.5)
      s.position.set(x, y)
      s.width = r * 2
      s.height = r * 2
      s.alpha = a
      s.blendMode = "add"
      this.nebula.addChild(s)
    }
    this.world.addChild(this.nebula)

    const p = new Sprite(planetTexture(512))
    p.anchor.set(0.5)
    p.position.set(-1500, 980)
    p.width = 2600
    p.height = 2600
    p.alpha = 0.85
    this.planetSprite = p
    this.world.addChild(p)

    const specs: [number, number, number, number][] = [
      [8801, 260, 1.2, 0.50],
      [9917, 200, 1.8, 0.62],
      [12043, 140, 2.6, 0.80],
      [13337, 60, 3.6, 0.95],
    ]
    for (const [seed, count, bright, alpha] of specs) {
      const ts = new TilingSprite({
        texture: starTile(seed, count, 512, alpha, bright),
        width: 4096,
        height: 4096,
      })
      this.stars.push(ts)
      this.world.addChild(ts)
    }

    this.container.addChild(this.world)
  }

  setSize(w: number, h: number): void {
    this.viewW = w
    this.viewH = h
    this.skySprite.width = w * 2.6
    this.skySprite.height = h * 2.6
    this.skySprite.position.set(0, 0)
    for (const s of this.stars) {
      s.width = w * 2.6
      s.height = h * 2.6
    }
  }

  update(camX: number, camY: number): void {
    this.sky.position.set(-camX * 0.04, -camY * 0.04)
    this.nebula.position.set(-camX * 0.18, -camY * 0.18)
    if (this.planetSprite) this.planetSprite.position.set(-1500 - camX * 0.10, 980 - camY * 0.10)
    for (let i = 0; i < this.stars.length; i++) {
      const f = this.parallax[i]
      const s = this.stars[i]
      s.position.set(-camX * f - this.viewW * (1 - f) / 2 + this.viewW / 2, -camY * f - this.viewH * (1 - f) / 2 + this.viewH / 2)
      s.tilePosition.set(camX * f * 0.4, camY * f * 0.4)
    }
  }
}
