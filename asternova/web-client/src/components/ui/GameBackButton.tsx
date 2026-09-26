"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { HudArrowLeft } from "@/src/components/icons/arcade-icons"

/**
 * 统一「返回大厅」按钮（Stage A 共享组件）
 * 替换全站 6 处各写各的返回按钮：xiaoxiaole / nova-ball / star-dash / merge / nebula 结算副按钮 / nova-ball 结算副按钮
 *
 * variant="header"  流式排版，放进 header / 工具栏
 * variant="floating" fixed 定位 + safe-area，适合纯 canvas / iframe 外壳（xiaoxiaole）
 *
 * 可靠性约定：
 * - 用 <a href> 原生导航兜底（JS/水合失败时仍可跳转），点击时 preventDefault 走 SPA 软导航
 * - floating 变体带 transform-gpu 提升独立合成层 + z-[160]，
 *   规避移动端 WebView（X5/旧WebKit）iframe 悬浮层吞点击的合成问题
 */
export function GameBackButton({
  variant = "header",
  label = "返回大厅",
  href = "/lobby",
  className,
}: {
  variant?: "header" | "floating"
  label?: string
  href?: string
  className?: string
}) {
  const router = useRouter()
  const base =
    "group relative inline-flex min-h-6 items-center gap-1.5 border border-hud-line bg-ink-800/80 px-3.5 py-2.5 text-[13px] font-medium text-hud-text backdrop-blur-glass-md transition-colors duration-fast hover:border-hud-accent/50 hover:text-hud-paper active:scale-[0.98] focus-visible:outline-none focus-visible:border-hud-accent before:absolute before:-inset-x-2 before:-inset-y-3 before:content-['']"
  const pos =
    variant === "floating"
      ? "fixed left-[max(0.75rem,env(safe-area-inset-left))] top-[max(0.75rem,env(safe-area-inset-top))] z-[160] transform-gpu pointer-events-auto bg-ink-900/85 shadow-lg"
      : ""
  return (
    <a
      href={href}
      draggable={false}
      onClick={(e) => {
        e.preventDefault()
        try {
          router.push(href)
        } catch {
          window.location.href = href
        }
      }}
      className={cn(base, pos, className)}
      aria-label={label}
    >
      <HudArrowLeft className="h-4 w-4 text-hud-accent transition-transform duration-fast group-hover:-translate-x-0.5" strokeWidth={1.75} />
      <span>{label}</span>
    </a>
  )
}
