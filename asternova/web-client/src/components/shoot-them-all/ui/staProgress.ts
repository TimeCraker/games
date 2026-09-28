/**
 * 弹珠风暴 —— 关卡进度持久化（选关屏 / 结算屏共用）
 *
 * 存储：localStorage["asternova.shoot-them-all.v1"]，独立于街机记录总线
 * （asternova.arcade.v1 只管历史最高分与局数，关卡星级 / 解锁是本作私有进度）。
 *
 * 健壮性照抄 src/components/arcade/records.ts：
 * - 写入失败（隐私模式 / 配额满）不抛异常，退化为内存态，本次会话内仍可读；
 * - 脏数据逐字段净化后保留，绝不因为一条坏记录把整块进度作废；
 * - 不引入 React（本文件可被非 React 侧 import），React 侧用 useStaProgress()。
 */

export const STA_PROGRESS_KEY = "asternova.shoot-them-all.v1"
export const STA_PROGRESS_VERSION = 1

/** 服务端 / 无进度态的统一快照（空串，避免 hydration mismatch） */
export const STA_EMPTY_SNAPSHOT = ""

export type StaLevelProgress = {
  /** 0~3 星（0 = 未通关） */
  stars: number
  /** 该关历史最佳分 */
  bestScore: number
  /** 是否已通关（决定下一关解锁） */
  cleared: boolean
  /** 是否可打。第 1 关恒 true；第 N 关在第 N-1 关 cleared 时置 true */
  unlocked: boolean
}

export type StaProgress = {
  version: number
  /** key = 关卡 id 的十进制字符串 */
  levels: Record<string, StaLevelProgress>
  /** 已看过的教学提示条 id（全局一次性，见 StaTutorialBar） */
  hintsSeen: string[]
}

function emptyProgress(): StaProgress {
  return { version: STA_PROGRESS_VERSION, levels: {}, hintsSeen: [] }
}

/* ------------------------------------------------------------------ */
/* 存储可用性探测 + 内存兜底                                            */
/* ------------------------------------------------------------------ */

const memFallback = new Map<string, string>()

const storageAvailable = (() => {
  if (typeof window === "undefined") return false
  try {
    const probe = "__asternova_sta_probe__"
    window.localStorage.setItem(probe, "1")
    window.localStorage.removeItem(probe)
    return true
  } catch {
    return false
  }
})()

function rawGet(): string {
  if (typeof window === "undefined") return ""
  if (!storageAvailable) return memFallback.get(STA_PROGRESS_KEY) ?? ""
  try {
    return window.localStorage.getItem(STA_PROGRESS_KEY) ?? ""
  } catch {
    return memFallback.get(STA_PROGRESS_KEY) ?? ""
  }
}

function rawSet(value: string): void {
  if (typeof window === "undefined") return
  memFallback.set(STA_PROGRESS_KEY, value)
  if (!storageAvailable) return
  try {
    window.localStorage.setItem(STA_PROGRESS_KEY, value)
  } catch {
    /* 配额满 / 隐私模式：保留内存态即可，不打断游戏 */
  }
}

/* ------------------------------------------------------------------ */
/* 解析 / 净化                                                         */
/* ------------------------------------------------------------------ */

function coerceLevel(v: unknown): StaLevelProgress | null {
  if (!v || typeof v !== "object") return null
  const o = v as Partial<StaLevelProgress>
  const starsRaw = typeof o.stars === "number" && Number.isFinite(o.stars) ? Math.floor(o.stars) : 0
  const bestScore =
    typeof o.bestScore === "number" && Number.isFinite(o.bestScore) ? Math.max(0, Math.floor(o.bestScore)) : 0
  return {
    stars: Math.max(0, Math.min(3, starsRaw)),
    bestScore,
    cleared: o.cleared === true,
    unlocked: o.unlocked === true,
  }
}

/**
 * 任意历史版本的原始串 → 当前结构。未知字段丢弃、坏字段回默认值。
 * 第 1 关恒解锁，且「已解锁」以「上一关已通关」为准做一次对账，
 * 避免只写 cleared 忘写 unlocked 之类不同步把玩家卡死。
 */
export function parseProgress(raw: string | null | undefined): StaProgress {
  if (!raw) return reconcile(emptyProgress())
  let parsed: unknown
  try {
    parsed = JSON.parse(raw)
  } catch {
    return reconcile(emptyProgress())
  }
  if (!parsed || typeof parsed !== "object") return reconcile(emptyProgress())
  const src = parsed as { levels?: unknown; hintsSeen?: unknown }

  const out = emptyProgress()
  out.version = STA_PROGRESS_VERSION

  const levels = src.levels
  if (levels && typeof levels === "object") {
    for (const [k, v] of Object.entries(levels as Record<string, unknown>)) {
      if (!/^\d+$/.test(k)) continue
      const rec = coerceLevel(v)
      if (rec) out.levels[k] = rec
    }
  }

  if (Array.isArray(src.hintsSeen)) {
    out.hintsSeen = src.hintsSeen.filter((x): x is string => typeof x === "string").slice(0, 32)
  }

  return reconcile(out)
}

/** 解锁对账：第 1 关恒开；第 N 关只要第 N-1 关已通关即视为可打。 */
function reconcile(p: StaProgress): StaProgress {
  const ids = Object.keys(p.levels)
    .map((k) => Number(k))
    .filter((n) => Number.isInteger(n) && n > 0)
    .sort((a, b) => a - b)

  const l1 = (p.levels["1"] ??= { stars: 0, bestScore: 0, cleared: false, unlocked: true })
  l1.unlocked = true

  // 只对已知的连续 id 段向前推导解锁；缺号的关（尚未打到）不凭空造记录。
  for (const id of ids) {
    const cur = p.levels[String(id)]
    const prev = p.levels[String(id - 1)]
    if (prev?.cleared) cur.unlocked = true
    if (cur.cleared) cur.unlocked = true
  }
  return p
}

/* ------------------------------------------------------------------ */
/* 读写                                                                */
/* ------------------------------------------------------------------ */

export function readProgress(): StaProgress {
  return parseProgress(rawGet())
}

export function readLevel(id: number): StaLevelProgress | null {
  return readProgress().levels[String(id)] ?? null
}

/** 该关是否可打：第 1 关恒可打，其余看解锁位。 */
export function isLevelUnlocked(id: number): boolean {
  if (id <= 1) return true
  return readProgress().levels[String(id)]?.unlocked === true
}

/**
 * 星级合计（选关屏 header 的 ★ n/30）。
 * 入参收 progress 而非自行 readProgress()：header 与卡面必须同源，
 * 否则响应式 store 与一次性读会渲染出两套数（实测 header 0/30 vs 卡面已亮星）。
 */
export function totalStars(p: StaProgress, maxLevels: number): number {
  let sum = 0
  for (let i = 1; i <= maxLevels; i++) sum += p.levels[String(i)]?.stars ?? 0
  return sum
}

export type LevelResultInput = {
  id: number
  stars: number
  score: number
  cleared: boolean
}

/**
 * 落一关的结算：星级取历史最大，分数取历史最大，通关后解锁下一关。
 * 返回写入后的进度，供 UI 立即刷新（不等下次读取）。
 */
export function recordLevelResult(input: LevelResultInput): StaProgress {
  const p = readProgress()
  const key = String(input.id)
  const prev = p.levels[key] ?? { stars: 0, bestScore: 0, cleared: false, unlocked: input.id <= 1 }
  const stars = Math.max(0, Math.min(3, Math.floor(input.stars)))
  const score = Math.max(0, Math.floor(input.score))
  const cleared = prev.cleared || input.cleared

  p.levels[key] = {
    stars: Math.max(prev.stars, stars),
    bestScore: Math.max(prev.bestScore, score),
    cleared,
    // 通关 / 星级到手即视为该关可打（防止 unlocked 漏写）
    unlocked: true,
  }

  // 解锁下一关
  const next = p.levels[String(input.id + 1)]
  if (next) {
    if (cleared) next.unlocked = true
  } else if (cleared) {
    p.levels[String(input.id + 1)] = { stars: 0, bestScore: 0, cleared: false, unlocked: true }
  }

  rawSet(JSON.stringify(p))
  notify()
  return p
}

/** 标记某条教学提示条已看过（同一条全局只出一次）。 */
export function markHintSeen(hintId: string): void {
  const p = readProgress()
  if (p.hintsSeen.includes(hintId)) return
  p.hintsSeen.push(hintId)
  rawSet(JSON.stringify(p))
  notify()
}

/** 清空本作进度（调试 / 设置用） */
export function clearStaProgress(): void {
  rawSet(JSON.stringify(emptyProgress()))
  notify()
}

/* ------------------------------------------------------------------ */
/* 订阅（配合 useSyncExternalStore）                                    */
/* ------------------------------------------------------------------ */

const listeners = new Set<() => void>()

function notify(): void {
  for (const l of listeners) l()
}

/** 供 useSyncExternalStore：用原始串当稳定快照 */
export function getSnapshot(): string {
  return rawGet()
}

export function getServerSnapshot(): string {
  return STA_EMPTY_SNAPSHOT
}

export function subscribe(onChange: () => void): () => void {
  listeners.add(onChange)
  let onStorage: ((e: StorageEvent) => void) | null = null
  if (typeof window !== "undefined") {
    onStorage = (e: StorageEvent) => {
      if (e.key === null || e.key === STA_PROGRESS_KEY) onChange()
    }
    window.addEventListener("storage", onStorage)
  }
  return () => {
    listeners.delete(onChange)
    if (typeof window !== "undefined" && onStorage) {
      window.removeEventListener("storage", onStorage)
    }
  }
}
