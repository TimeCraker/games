/**
 * 确定性随机（mulberry32）——模拟核心内**禁止** Math.random / Date.now，
 * 否则回放与快照 hash 不可能一致（白皮书 §11.9）。
 */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/** 一个可序列化的随机源，模拟持有它即可完全复现 */
export class Rng {
  private next: () => number
  constructor(public readonly seed: number) {
    this.next = mulberry32(seed)
  }
  f(): number { return this.next() }
  range(a: number, b: number): number { return a + this.next() * (b - a) }
  int(a: number, b: number): number { return Math.floor(this.range(a, b + 1)) }
  pick<T>(arr: readonly T[]): T { return arr[Math.floor(this.next() * arr.length)] }
  /** 单位圆内均匀取点 */
  unit(): { x: number; y: number } {
    const a = this.next() * Math.PI * 2
    const r = Math.sqrt(this.next())
    return { x: Math.cos(a) * r, y: Math.sin(a) * r }
  }
  /** 状态导出：用于测试断言与调试 */
  snapshot(): number { return this.seed }
}
