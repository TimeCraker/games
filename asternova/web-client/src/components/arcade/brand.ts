/**
 * AsterNova Arcade · 品牌单一真源（Single Source of Truth）
 *
 * 大厅卡片、5 个游戏路由的 metadata、游戏内开场/结算品牌字，全部从这里派生。
 *
 * 起因（2026-09-27 取证）：上一轮只重构了 /lobby 的命名，游戏路由全线没跟上，
 * 实测出现「大厅叫『Shoot Them All / 弹珠风暴』、页面 title 却是『射击大战』」
 * 这类断层。此后**禁止**在这些位置硬写中英文名，一律走本文件。
 *
 * 约束：本文件必须保持「纯数据」——不得引入 React 组件、hooks 或浏览器 API。
 *       5 个 app/<route>/page.tsx 是服务端组件，会 import 它来生成 metadata。
 */

import type { KeyArtSlug } from "@/src/lib/keyArt"

export const ARCADE_SLUGS = [
  "nebula-survivor",
  "shoot-them-all",
  "lets-running",
  "merge",
  "xiaoxiaole",
] as const

export type ArcadeSlug = (typeof ARCADE_SLUGS)[number]

/**
 * 编译期哨兵：本文件的 5 个 slug 必须与产图脚本生成的 KeyArtSlug
 * （src/lib/keyArt.ts，由 scripts/fetch-arcade-art.mjs 写入）完全一致。
 * 任何一边增删游戏而另一边没跟上，这里会直接报类型错误。
 * import type 会在编译期被擦除，不会把 LQIP base64 带进运行时。
 */
type Assert<T extends true> = T
export type _SlugParityWithKeyArt = Assert<
  [ArcadeSlug] extends [KeyArtSlug] ? ([KeyArtSlug] extends [ArcadeSlug] ? true : false) : false
>

/** 副强调色在 globals.css 里的变量名（低饱和，与琥珀同亮度带） */
export type ArcadeAccentVar =
  | "--arcade-nebula"
  | "--arcade-shoot"
  | "--arcade-running"
  | "--arcade-merge"
  | "--arcade-matrix"

export type ArcadeBrand = {
  slug: ArcadeSlug
  /** 站内路由 */
  href: string
  /** 卡片角标序号（大厅 01–05） */
  index: string
  /** 玩法分类（卡片右上角，英文短标签） */
  category: string
  /** 英文主名（游戏内主标题、metadata title 前半段） */
  titleEn: string
  /** 中文标注（紧跟英文主名，直观易懂） */
  titleZh: string
  /** 一句话玩法说明 */
  tagline: string
  /** 本游戏的副强调色变量名 */
  accentVar: ArcadeAccentVar
  /** 大厅精选位（跨两列的旗舰卡） */
  featured?: boolean
}

/**
 * 5 个街机作品的品牌定义。
 * ⚠️ 顺序即大厅展示顺序；featured 只应有一个（当前为 nebula-survivor）。
 */
export const ARCADE_BRAND: Record<ArcadeSlug, ArcadeBrand> = {
  "nebula-survivor": {
    slug: "nebula-survivor",
    href: "/nebula-survivor",
    index: "01",
    category: "Survivor",
    titleEn: "Nebula Survivor",
    titleZh: "星域突围",
    tagline: "俯视角肉鸽 · 三选一构筑 · 五条强化轨道",
    accentVar: "--arcade-nebula",
    featured: true,
  },
  "shoot-them-all": {
    slug: "shoot-them-all",
    href: "/shoot-them-all",
    index: "02",
    category: "Physics",
    titleEn: "Shoot Them All",
    titleZh: "弹珠风暴",
    tagline: "物理弹射 · 连锁清场",
    accentVar: "--arcade-shoot",
  },
  "lets-running": {
    slug: "lets-running",
    href: "/lets-running",
    index: "03",
    category: "Runner",
    titleEn: "Let's Running",
    titleZh: "星轨疾驰",
    tagline: "跑酷滑铲 · 极限冲刺",
    accentVar: "--arcade-running",
  },
  merge: {
    slug: "merge",
    href: "/merge",
    index: "04",
    category: "Merge",
    titleEn: "AsterNova Merge",
    titleZh: "星核进化",
    tagline: "合成星球 · 十级进化",
    accentVar: "--arcade-merge",
  },
  xiaoxiaole: {
    slug: "xiaoxiaole",
    href: "/xiaoxiaole",
    index: "05",
    category: "Match-3",
    titleEn: "StarMatrix",
    titleZh: "星阵消消乐",
    tagline: "立体三消 · 12 关闯关",
    accentVar: "--arcade-matrix",
  },
}

/** 大厅 / 遍历用的有序列表 */
export const ARCADE_LIST: ArcadeBrand[] = ARCADE_SLUGS.map((s) => ARCADE_BRAND[s])

/**
 * 统一展示名：「英文主名 · 中文标注」。
 * metadata.title 与游戏内开场品牌字都用它，保证任意位置读到的都是同一个名字。
 */
export function arcadeDisplayName(slug: ArcadeSlug): string {
  const b = ARCADE_BRAND[slug]
  return `${b.titleEn} · ${b.titleZh}`
}

/**
 * 给 app/<route>/page.tsx 的 metadata.title 用。
 * 交给根 layout 的 template「%s · AsterNova」补品牌后缀，
 * 因此这里绝不能自带「· AsterNova」，否则会重复。
 */
export function arcadeMetadataTitle(slug: ArcadeSlug): string {
  return arcadeDisplayName(slug)
}
