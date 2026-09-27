import { describe, expect, it } from "vitest"

import { FIXED_DT, Sim } from "./Sim"
import { MERGE_REQUIRED, MAX_STARS } from "../content/weapons"
import { CLASS_IDS } from "../content/classes"

/**
 * 固定步长推进 n 秒（模拟真实累加器行为）。
 * 波次结束会开商店并暂停模拟 —— 这是正确的产品行为，测试里模拟玩家立刻关掉它，
 * 否则步数会被商店吃掉（曾据此踩过一次错误的断言）。
 */
function run(sim: Sim, seconds: number, input: (t: number) => { x: number; y: number } = () => ({ x: 0, y: 0 })) {
  const steps = Math.round(seconds / FIXED_DT)
  for (let i = 0; i < steps; i++) {
    if (sim.shopOpen) sim.closeShop()
    const m = input(i * FIXED_DT)
    sim.setMove(m.x, m.y)
    sim.step()
  }
}

describe("Sim · 确定性", () => {
  it("同种子 + 同输入流 → 快照 hash 完全一致", () => {
    const input = (t: number) => ({ x: Math.cos(t * 1.7), y: Math.sin(t * 1.1) })
    const a = new Sim({ seed: 20260927, classId: "gunner" })
    const b = new Sim({ seed: 20260927, classId: "gunner" })
    run(a, 30, input)
    run(b, 30, input)
    expect(a.hashSnapshot()).toBe(b.hashSnapshot())
    expect(a.kills).toBe(b.kills)
    expect(a.tick).toBe(b.tick)
  })

  it("不同种子 → 快照 hash 不同（防止漏接随机源）", () => {
    const a = new Sim({ seed: 1, classId: "brawler" })
    const b = new Sim({ seed: 2, classId: "brawler" })
    run(a, 20)
    run(b, 20)
    expect(a.hashSnapshot()).not.toBe(b.hashSnapshot())
  })

  it("模拟内不依赖真实时间：tick 与 time 严格成 fixed-dt 关系", () => {
    // 注意：原地不动会被围死（gameOver 后不再推进），所以取一段必定存活的时长。
    const s = new Sim({ seed: 7, classId: "tank" })
    run(s, 20)
    expect(s.tick).toBe(20 * 60)
    // 这条才是真正的「步长固定」断言：time 由 tick 推出，与墙上时钟无关
    expect(s.time).toBeCloseTo(s.tick * FIXED_DT, 10)
  })
})

describe("Sim · 竞技场与碰撞", () => {
  it("玩家被硬边界挡住，不会跑出竞技场", () => {
    const s = new Sim({ seed: 3, classId: "skirmisher" })
    run(s, 40, () => ({ x: 1, y: 0 }))
    expect(Math.abs(s.player.x)).toBeLessThanOrEqual(s.arena.halfW)
    expect(Math.abs(s.player.y)).toBeLessThanOrEqual(s.arena.halfH)
  })

  it("玩家不会卡进障碍物内部", () => {
    const s = new Sim({ seed: 11, classId: "brawler" })
    // 朝左上角的大型舱段直冲
    run(s, 25, () => ({ x: -0.72, y: -0.7 }))
    for (const o of s.arena.obstacles) {
      if (o.kind === "rect") {
        const inside =
          s.player.x > o.x + 1 && s.player.x < o.x + o.w - 1 &&
          s.player.y > o.y + 1 && s.player.y < o.y + o.h - 1
        expect(inside).toBe(false)
      } else {
        const d = Math.hypot(s.player.x - o.x, s.player.y - o.y)
        expect(d).toBeGreaterThanOrEqual(o.r - 1)
      }
    }
  })
})

describe("Sim · 武器三合一（白皮书 §5.3）", () => {
  it("3 个同名同星 → 升 1 星，计数清零", () => {
    const s = new Sim({ seed: 5, classId: "gunner" })
    const first = s.weapons[0].id
    s.acquireWeapon(first)
    s.acquireWeapon(first)
    expect(s.weapons[0].stars).toBe(1)
    expect(s.weapons[0].mergeCount).toBe(2)
    s.acquireWeapon(first)
    expect(s.weapons[0].stars).toBe(2)
    expect(s.weapons[0].mergeCount).toBe(0)
  })

  it("槽位只有 3 个：第 4 把不同武器转为金币而非丢弃", () => {
    const s = new Sim({ seed: 9, classId: "brawler" })
    const pool = s.cls.weapons
    s.acquireWeapon(pool[1])
    s.acquireWeapon(pool[2])
    const before = s.coins
    s.acquireWeapon(pool[0]) // 已持有 → 走三合一
    expect(s.weapons.length).toBe(3)
    expect(s.coins).toBeGreaterThanOrEqual(before)
  })

  it("满星后继续拾取不再溢出", () => {
    const s = new Sim({ seed: 13, classId: "gunner" })
    const id = s.weapons[0].id
    for (let i = 0; i < 200; i++) s.acquireWeapon(id)
    expect(s.weapons[0].stars).toBeLessThanOrEqual(MAX_STARS)
  })

  it("花金币直升 1 星需要足够金币", () => {
    const s = new Sim({ seed: 17, classId: "gravity" })
    const id = s.weapons[0].id
    expect(s.upgradeWeapon(id)).toBe(false) // 没钱
    s.coins = 100000
    expect(s.upgradeWeapon(id)).toBe(true)
    expect(s.weapons[0].stars).toBe(2)
  })
})

describe("Sim · 五个职业都能开局并存活", () => {
  it.each(CLASS_IDS)("%s：开局有 1 把武器，跑 20 秒不崩", (cid) => {
    const s = new Sim({ seed: 42, classId: cid })
    expect(s.weapons.length).toBe(1)
    run(s, 20)
    expect(s.time).toBeGreaterThan(19)
    expect(Number.isFinite(s.player.x)).toBe(true)
    expect(Number.isFinite(s.player.hp)).toBe(true)
  })
})
