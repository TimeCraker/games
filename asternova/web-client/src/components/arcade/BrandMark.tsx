"use client"

import { cn } from "@/lib/utils"

import { ARCADE_BRAND, type ArcadeSlug } from "./brand"

/**
 * 统一的游戏品牌标记：「英文主名 + 中文标注」。
 *
 * 3 个变体覆盖了此前 5 个游戏各写各的全部场景：
 * - `strip`  画布角落 / HUD 角的等宽小字（原 "SHOOT THEM ALL · V2"）
 * - `title`  开场与结算的大字号（原 canvas fillText 的渐变标题）
 * - `inline` 规则卡、页脚的一行式（原 "AsterNova · Merge · 星球合成"）
 *
 * 名字一律从 brand.ts 取，禁止在这里或调用处硬写。
 * 副强调色走 --arcade-accent，由 ArcadeShell 按游戏作用域注入，默认回落琥珀。
 */
export function BrandMark({
  slug,
  variant = "strip",
  className,
  /** 渲染元素。title 变体需要承担页面的 h2 语义（merge 的面板标题就是 h2）。 */
  as: As = "span",
}: {
  slug: ArcadeSlug
  variant?: "strip" | "title" | "inline"
  className?: string
  as?: "span" | "h2"
}) {
  const brand = ARCADE_BRAND[slug]
  const accent = "text-[color:var(--arcade-accent)]"

  if (variant === "title") {
    return (
      <As className={cn("flex flex-col items-center text-center", className)}>
        <span className="font-display text-2xl font-bold leading-[1.1] tracking-tight text-hud-paper sm:text-[1.75rem]">
          {brand.titleEn}
        </span>
        <span className={cn("mt-1 text-[13px] font-medium tracking-wide", accent)}>{brand.titleZh}</span>
      </As>
    )
  }

  if (variant === "inline") {
    return (
      <As className={cn("inline-flex items-center gap-2", className)}>
        <span className="font-medium text-hud-text-dim">{brand.titleEn}</span>
        <span className={cn("font-medium", accent)}>{brand.titleZh}</span>
      </As>
    )
  }

  return (
    <As className={cn("inline-flex items-center gap-2", className)}>
      <span className="font-mono-data text-[10px] uppercase tracking-[0.22em] text-hud-text-faint">
        {brand.titleEn}
      </span>
      <span className={cn("font-mono-data text-[10px] tracking-[0.18em]", accent)}>{brand.titleZh}</span>
    </As>
  )
}
