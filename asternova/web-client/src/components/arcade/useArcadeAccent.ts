"use client"

import * as React from "react"

import { ARCADE_BRAND, type ArcadeSlug } from "./brand"

/**
 * 把某游戏的副强调色挂到 <html> 上（并卸载时还原）。
 *
 * 为什么需要它，而不能只靠根节点上的 inline style：
 * 游戏的规则弹层、结算卡、悬浮返回钮都通过 StagePortal 渲染到 document.body，
 * 而 **CSS 自定义属性不会跨 portal 边界继承** —— 挂在游戏根节点上的
 * `--arcade-accent` 对 portal 里的子树完全不可见，会静默回落成 :root 的琥珀。
 * （2026-09-27 实测踩到：结算卡里的「星轨疾驰」应是冰蓝，实际渲染成金色。）
 *
 * 两者并存：根节点 inline style 负责首帧（在 effect 之前）就正确，
 * 本 hook 负责覆盖 portal 子树。卸载时移除行内属性，恢复 :root 的琥珀兜底。
 */
export function useArcadeAccent(slug: ArcadeSlug): void {
  React.useEffect(() => {
    const el = document.documentElement
    const prev = el.style.getPropertyValue("--arcade-accent")
    el.style.setProperty("--arcade-accent", `var(${ARCADE_BRAND[slug].accentVar})`)
    return () => {
      if (prev) el.style.setProperty("--arcade-accent", prev)
      else el.style.removeProperty("--arcade-accent")
    }
  }, [slug])
}
