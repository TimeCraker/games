"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cinematicEase } from "@/src/lib/motion"

/**
 * 玻璃质感面板（从 app/lobby/page.tsx 抽离，全站共享）
 * motion 入场 + backdrop-blur + 内描边高光
 */
export function GlassPanel({
  children,
  className = "",
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.5, ease: cinematicEase }}
      className={`rounded-[1.35rem] border border-white/[0.08] bg-white/[0.04] shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] backdrop-blur-2xl ${className}`}
      style={{ WebkitBackdropFilter: "blur(40px) saturate(180%)" }}
    >
      {children}
    </motion.div>
  )
}
