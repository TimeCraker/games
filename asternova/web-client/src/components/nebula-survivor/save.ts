/**
 * 星域突围 · 局外存档（独立命名空间 `asternova.nebula.v1`）
 *
 * 与街机分数总线 `asternova.arcade.v1` **正交**：后者被 ArcadeRecord 强类型锁死
 * （best / plays / lastRoundId），塞元进度会污染另外四个游戏（白皮书 §15）。
 *
 * 健壮性照抄 components/arcade/records.ts：写入失败不抛异常，
 * 隐私模式 / 配额满退化为内存态；坏数据逐字段净化，绝不整体作废。
 *
 * 约束：本文件不得引入 React（可能被服务端间接 import）。
 */
import { CLASS_IDS, DEFAULT_CLASS } from "./content/classes"
import { MAX_STARS, WEAPON_IDS } from "./content/weapons"
import { ESKILL_IDS } from "./content/eskills"
import type { ClassId, ESkillId, WeaponId } from "./sim/types"

export const SAVE_KEY = "asternova.nebula.v1"
export const SAVE_VERSION = 1
const CHANGE_EVENT = "asternova:nebula-save"

export type NebulaSave = {
  version: number
  /** 局外货币 */
  coins: number
  /** 局外经验（升基础数值） */
  xp: number
  /** 各职业已投入的等级（1 = 未强化） */
  classLevels: Record<ClassId, number>
  /** 各武器已解锁的起始星级（局内仍可继续升） */
  weaponStars: Partial<Record<WeaponId, number>>
  /** 各 E 技等级 */
  eskills: Record<ESkillId, number>
  /** 上次选择的职业 */
  lastClass: ClassId
  /** 累计局数 / 击杀 */
  runs: number
  totalKills: number
}

function emptySave(): NebulaSave {
  const classLevels = {} as Record<ClassId, number>
  for (const c of CLASS_IDS) classLevels[c] = 1
  const eskills = {} as Record<ESkillId, number>
  for (const e of ESKILL_IDS) eskills[e] = 1
  return {
    version: SAVE_VERSION, coins: 0, xp: 0,
    classLevels, weaponStars: {}, eskills,
    lastClass: DEFAULT_CLASS, runs: 0, totalKills: 0,
  }
}

/* ------------------------------ 存储与兜底 ------------------------------ */

const mem = new Map<string, string>()

const storageAvailable = (() => {
  if (typeof window === "undefined") return false
  try {
    const probe = "__asternova_nebula_probe__"
    window.localStorage.setItem(probe, "1")
    window.localStorage.removeItem(probe)
    return true
  } catch { return false }
})()

function rawGet(): string {
  if (typeof window === "undefined") return ""
  if (!storageAvailable) return mem.get(SAVE_KEY) ?? ""
  try { return window.localStorage.getItem(SAVE_KEY) ?? "" } catch { return mem.get(SAVE_KEY) ?? "" }
}
function rawSet(v: string): void {
  if (typeof window === "undefined") return
  mem.set(SAVE_KEY, v)
  if (!storageAvailable) return
  try { window.localStorage.setItem(SAVE_KEY, v) } catch { /* 配额满 / 隐私模式 */ }
}

/* ------------------------------ 净化 ------------------------------ */

const num = (v: unknown, d = 0): number =>
  typeof v === "number" && Number.isFinite(v) ? Math.max(0, Math.floor(v)) : d

export function parseSave(raw: string | null | undefined): NebulaSave {
  const out = emptySave()
  if (!raw) return out
  let parsed: unknown
  try { parsed = JSON.parse(raw) } catch { return out }
  if (!parsed || typeof parsed !== "object") return out
  const s = parsed as Record<string, unknown>

  out.coins = num(s.coins)
  out.xp = num(s.xp)
  out.runs = num(s.runs)
  out.totalKills = num(s.totalKills)
  if (typeof s.lastClass === "string" && (CLASS_IDS as readonly string[]).includes(s.lastClass)) {
    out.lastClass = s.lastClass as ClassId
  }
  if (s.classLevels && typeof s.classLevels === "object") {
    for (const c of CLASS_IDS) {
      const v = (s.classLevels as Record<string, unknown>)[c]
      out.classLevels[c] = Math.min(60, Math.max(1, num(v, 1)))
    }
  }
  if (s.eskills && typeof s.eskills === "object") {
    for (const e of ESKILL_IDS) {
      const v = (s.eskills as Record<string, unknown>)[e]
      out.eskills[e] = Math.min(20, Math.max(1, num(v, 1)))
    }
  }
  if (s.weaponStars && typeof s.weaponStars === "object") {
    for (const id of WEAPON_IDS) {
      const v = (s.weaponStars as Record<string, unknown>)[id]
      if (typeof v === "number" && Number.isFinite(v) && v >= 1) {
        out.weaponStars[id] = Math.min(MAX_STARS, Math.max(1, Math.floor(v)))
      }
    }
  }
  out.version = SAVE_VERSION
  return out
}

/* ------------------------------ 读写 ------------------------------ */

export function readSave(): NebulaSave { return parseSave(rawGet()) }

export function writeSave(mutate: (s: NebulaSave) => void): NebulaSave {
  const s = readSave()
  mutate(s)
  s.version = SAVE_VERSION
  rawSet(JSON.stringify(s))
  notify()
  return s
}

/** 局外经验 → 基础数值加成（白皮书 §9） */
export function derived(s: NebulaSave): { damage: number; armor: number; spell: number } {
  return {
    damage: s.xp * 0.002,
    armor: Math.min(0.12, s.xp * 0.00035),
    spell: s.xp * 0.002,
  }
}

export function resetSave(): void {
  rawSet(JSON.stringify(emptySave()))
  notify()
}

/* ------------------------------ 订阅 ------------------------------ */

const listeners = new Set<() => void>()
function notify(): void { for (const l of listeners) l() }

export function getSnapshot(): string { return rawGet() }
export function getServerSnapshot(): string { return "" }

export function subscribe(onChange: () => void): () => void {
  listeners.add(onChange)
  let onStorage: ((e: StorageEvent) => void) | null = null
  if (typeof window !== "undefined") {
    onStorage = (e: StorageEvent) => { if (e.key === null || e.key === SAVE_KEY) onChange() }
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
