import type { CSSProperties } from "react"

import { ARCADE_BRAND, type ArcadeSlug } from "./brand"

/**
 * 把某个游戏的副强调色注入为作用域 CSS 变量 `--arcade-accent`。
 *
 * 用法：<div style={arcadeAccentStyle("merge")}> … 子树里任意元素即可用
 * `text-[color:var(--arcade-accent)]` / `border-[color:var(--arcade-accent)]` 取到本游戏副色。
 *
 * 之所以用「作用域 CSS 变量」而不是 `text-arcade-merge` 这类动态类名：
 * Tailwind 无法为运行时拼接的类名生成样式，而品牌标记要能在 5 个游戏里复用同一个组件。
 * 未注入时 `--arcade-accent` 在 :root 回落为琥珀，因此漏注入只会退化成金色而非崩坏。
 */
export function arcadeAccentStyle(slug: ArcadeSlug): CSSProperties {
  return { ["--arcade-accent"]: `var(${ARCADE_BRAND[slug].accentVar})` } as CSSProperties
}
