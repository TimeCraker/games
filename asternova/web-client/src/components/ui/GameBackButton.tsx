"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft } from "lucide-react"
import { cn } from "@/lib/utils"

/**
 * 统一「返回大厅」按钮（Stage A 共享组件）
 * 替换全站 6 处各写各的返回按钮：xiaoxiaole / nova-ball / star-dash / merge / nebula 结算副按钮 / nova-ball 结算副按钮
 *
 * variant="header"  流式排版，放进 header / 工具栏
 * variant="floating" fixed 定位 + safe-area，适合纯 canvas / iframe 外壳（xiaoxiaole）
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
    "group inline-flex items-center gap-1.5 rounded-full border border-glass-border bg-glass-bg px-3.5 py-2 text-[13px] font-medium text-white/90 backdrop-blur-glass-md shadow-sm transition-colors duration-fast hover:bg-white/10 hover:text-white active:scale-[0.98]"
  const pos =
    variant === "floating"
      ? "fixed left-[max(0.75rem,env(safe-area-inset-left))] top-[max(0.75rem,env(safe-area-inset-top))] z-50"
      : "relative"
  return (
    <button
      type="button"
      onClick={() => router.push(href)}
      className={cn(base, pos, className)}
      aria-label={label}
    >
      <ArrowLeft className="h-4 w-4 transition-transform duration-fast group-hover:-translate-x-0.5" />
      <span>{label}</span>
    </button>
  )
}
