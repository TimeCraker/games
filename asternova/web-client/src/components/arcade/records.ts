/**
 * AsterNova Arcade · 本地记录总线（单命名空间）
 *
 * 现状（2026-09-27 取证）：5 个游戏里 4 个 React 游戏只往 localStorage 写了
 * 「不再显示规则」的 flag，**零分数、零进度**；大厅卡片也没有记录位。
 * 本模块提供全街机唯一的记录入口，游戏结束时 submitRecord()，大厅卡片读 best。
 *
 * 存储：localStorage["asternova.arcade.v1"]，带 version + migrate 兜底。
 * 健壮性照抄 public/xiaoxiaole/game.js 的写法：写入失败不抛异常，
 * 隐私模式/配额满时退化为内存态（本次会话内仍可读）。
 *
 * 约束：本文件不得引入 React（服务端可能间接 import）。React 侧的订阅
 *       请用 useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)。
 */

import { ARCADE_SLUGS, type ArcadeSlug } from "./brand"

export const ARCADE_RECORDS_KEY = "asternova.arcade.v1"
export const ARCADE_RECORDS_VERSION = 1

/** 内部变更 / 跨标签页同步用的广播事件名 */
const CHANGE_EVENT = "asternova:arcade-records"

/** 服务端与「无记录」态的统一快照：空串（避免 hydration mismatch） */
export const EMPTY_SNAPSHOT = ""

export type ArcadeRecord = {
  /** 历史最高分 */
  best: number
  /** 取得最高分时的模式（如 "endless" / "daily"，无模式则空） */
  bestMode: string
  /** 累计游玩局数 */
  plays: number
  /** 最近一次游玩时间戳（ms） */
  lastPlayedAt: number
}

export type ArcadeRecords = {
  version: number
  games: Partial<Record<ArcadeSlug, ArcadeRecord>>
}

function emptyRecords(): ArcadeRecords {
  return { version: ARCADE_RECORDS_VERSION, games: {} }
}

/* ------------------------------------------------------------------ */
/* 存储可用性探测 + 内存兜底                                            */
/* ------------------------------------------------------------------ */

const memFallback = new Map<string, string>()

const storageAvailable = (() => {
  if (typeof window === "undefined") return false
  try {
    const probe = "__asternova_probe__"
    window.localStorage.setItem(probe, "1")
    window.localStorage.removeItem(probe)
    return true
  } catch {
    return false
  }
})()

function rawGet(): string {
  if (typeof window === "undefined") return ""
  if (!storageAvailable) return memFallback.get(ARCADE_RECORDS_KEY) ?? ""
  try {
    return window.localStorage.getItem(ARCADE_RECORDS_KEY) ?? ""
  } catch {
    return memFallback.get(ARCADE_RECORDS_KEY) ?? ""
  }
}

function rawSet(value: string): void {
  if (typeof window === "undefined") return
  memFallback.set(ARCADE_RECORDS_KEY, value)
  if (!storageAvailable) return
  try {
    window.localStorage.setItem(ARCADE_RECORDS_KEY, value)
  } catch {
    /* 配额满 / 隐私模式：保留内存态即可，不打断游戏 */
  }
}

/* ------------------------------------------------------------------ */
/* 解析 / 迁移                                                         */
/* ------------------------------------------------------------------ */

function isSlug(v: unknown): v is ArcadeSlug {
  return typeof v === "string" && (ARCADE_SLUGS as readonly string[]).includes(v)
}

function coerceRecord(v: unknown): ArcadeRecord | null {
  if (!v || typeof v !== "object") return null
  const o = v as Partial<ArcadeRecord>
  const best = typeof o.best === "number" && Number.isFinite(o.best) ? Math.max(0, Math.floor(o.best)) : 0
  const plays = typeof o.plays === "number" && Number.isFinite(o.plays) ? Math.max(0, Math.floor(o.plays)) : 0
  const lastPlayedAt =
    typeof o.lastPlayedAt === "number" && Number.isFinite(o.lastPlayedAt) ? o.lastPlayedAt : 0
  const bestMode = typeof o.bestMode === "string" ? o.bestMode : ""
  return { best, bestMode, plays, lastPlayedAt }
}

/**
 * 把任意历史版本的原始串解析成当前结构。
 * 未知 slug 与坏字段一律丢弃，绝不因为脏数据把整个记录块作废。
 */
export function parseRecords(raw: string | null | undefined): ArcadeRecords {
  if (!raw) return emptyRecords()
  let parsed: unknown
  try {
    parsed = JSON.parse(raw)
  } catch {
    return emptyRecords()
  }
  if (!parsed || typeof parsed !== "object") return emptyRecords()
  const src = parsed as { version?: unknown; games?: unknown }

  // v1 起结构一致；此处只做「逐字段净化 + 未知 slug 丢弃」，
  // 后续若升到 v2，在此按 version 分派迁移函数即可。
  const out = emptyRecords()
  out.version = ARCADE_RECORDS_VERSION
  const games = src.games
  if (games && typeof games === "object") {
    for (const [k, v] of Object.entries(games as Record<string, unknown>)) {
      if (!isSlug(k)) continue
      const rec = coerceRecord(v)
      if (rec) out.games[k] = rec
    }
  }
  return out
}

/* ------------------------------------------------------------------ */
/* 读写                                                                */
/* ------------------------------------------------------------------ */

export function readRecords(): ArcadeRecords {
  return parseRecords(rawGet())
}

export function readRecord(slug: ArcadeSlug): ArcadeRecord | null {
  return readRecords().games[slug] ?? null
}

/** 大厅卡片用：拿最高分（无记录返回 null，好让卡片不渲染徽标而非渲染 0） */
export function bestScore(slug: ArcadeSlug): number | null {
  const rec = readRecord(slug)
  return rec && rec.best > 0 ? rec.best : null
}

export type SubmitResult = {
  record: ArcadeRecord
  /** 本局是否刷新了历史最高（用于结算卡 NEW RECORD 标记） */
  isNewBest: boolean
  /** 是否为首局（用于文案区分） */
  isFirstPlay: boolean
}

/**
 * 提交一局结果。分数为 0 也会累计 plays（用户确实玩了一局）。
 * 返回写入后的记录与「是否破纪录」，供结算卡即时展示。
 */
export function submitRecord(
  slug: ArcadeSlug,
  input: { score: number; mode?: string },
): SubmitResult {
  const all = readRecords()
  const prev = all.games[slug] ?? null
  const score = Number.isFinite(input.score) ? Math.max(0, Math.floor(input.score)) : 0
  const isNewBest = prev === null || score > prev.best

  const next: ArcadeRecord = {
    best: prev ? Math.max(prev.best, score) : score,
    bestMode: isNewBest ? (input.mode ?? "") : (prev?.bestMode ?? ""),
    plays: (prev?.plays ?? 0) + 1,
    lastPlayedAt: Date.now(),
  }
  all.games[slug] = next
  rawSet(JSON.stringify(all))
  notify()
  return { record: next, isNewBest: isNewBest && score > 0, isFirstPlay: prev === null }
}

/** 清空全部街机记录（设置面板/调试用） */
export function clearRecords(): void {
  rawSet(JSON.stringify(emptyRecords()))
  notify()
}

/* ------------------------------------------------------------------ */
/* 订阅（配合 useSyncExternalStore）                                    */
/* ------------------------------------------------------------------ */

const listeners = new Set<() => void>()

function notify(): void {
  for (const l of listeners) l()
}

/** 供 useSyncExternalStore 使用：返回原始串作为稳定快照 */
export function getSnapshot(): string {
  return rawGet()
}

/** 服务端快照：固定空串，保证 SSR 输出与首帧一致 */
export function getServerSnapshot(): string {
  return EMPTY_SNAPSHOT
}

/**
 * 订阅记录变更：既收本标签页的写入广播，也收跨标签页的 storage 事件。
 * 返回取消订阅函数。
 */
export function subscribe(onChange: () => void): () => void {
  listeners.add(onChange)
  let onStorage: ((e: StorageEvent) => void) | null = null
  if (typeof window !== "undefined") {
    onStorage = (e: StorageEvent) => {
      if (e.key === null || e.key === ARCADE_RECORDS_KEY) onChange()
    }
    window.addEventListener("storage", onStorage)
    window.addEventListener(CHANGE_EVENT, onChange)
  }
  return () => {
    listeners.delete(onChange)
    if (typeof window !== "undefined" && onStorage) {
      window.removeEventListener("storage", onStorage)
      window.removeEventListener(CHANGE_EVENT, onChange)
    }
  }
}

/** 千分位格式化（大厅徽标与结算卡共用） */
export function formatScore(n: number): string {
  return n.toLocaleString("en-US")
}
