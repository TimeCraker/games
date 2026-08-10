import type Matter from "matter-js"

export type EntityKind =
  | "ball"
  | "peg-crystal"
  | "peg-resonance"
  | "peg-life"
  | "peg-pulsar"
  | "peg-magnetar"
  | "peg-supernova"
  | "well"
  | "enemy"

export interface Entity {
  /** matter body.id，唯一 */
  id: number
  kind: EntityKind
  body: Matter.Body
  hp: number
  alive: boolean
  /** 游戏状态附加（如敌人充能、钉子倍率档），不持 sprite（渲染层自管） */
  meta?: Record<string, unknown>
}

/**
 * Entity 注册表（Stage Spec §8.4）。
 * 引擎层零 Pixi 依赖：只存 body + 游戏状态；渲染层另持 bodyId→sprite 映射。
 * 按类型分桶 O(1) 查询，替代每帧 Composite.allBodies().filter() 全表扫。
 */
export class EntityRegistry {
  private byId = new Map<number, Entity>()
  private byKind = new Map<EntityKind, Set<Entity>>()

  register(e: Entity): void {
    this.byId.set(e.id, e)
    let bucket = this.byKind.get(e.kind)
    if (!bucket) {
      bucket = new Set()
      this.byKind.set(e.kind, bucket)
    }
    bucket.add(e)
  }

  unregister(id: number): void {
    const e = this.byId.get(id)
    if (!e) return
    this.byId.delete(id)
    this.byKind.get(e.kind)?.delete(e)
  }

  get(id: number): Entity | undefined {
    return this.byId.get(id)
  }

  ofKind(kind: EntityKind): Entity[] {
    return [...(this.byKind.get(kind) ?? [])]
  }

  /** 所有存活实体（含静态钉子） */
  all(): Entity[] {
    return [...this.byId.values()]
  }

  countKind(kind: EntityKind): number {
    return this.byKind.get(kind)?.size ?? 0
  }

  clear(): void {
    this.byId.clear()
    this.byKind.clear()
  }
}
