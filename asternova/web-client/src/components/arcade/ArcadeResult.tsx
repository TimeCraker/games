"use client"

import * as React from "react"

import { ResultOverlay, type ResultStat } from "@/src/components/ui/ResultOverlay"

import { BrandMark } from "./BrandMark"
import type { ArcadeSlug } from "./brand"
import { formatScore, newRoundId, submitRecord } from "./records"

/**
 * 街机统一结算。
 *
 * 在既有 ResultOverlay 之上补三件此前每个游戏都缺或各写各的东西：
 * 1. 品牌标记（英文主名 + 中文标注，取 brand.ts）；
 * 2. 本局得分 + 历史最高的并排读数（历史最高来自 asternova.arcade.v1）；
 * 3. NEW RECORD 标记。
 *
 * 落盘时机：挂在 useState 初始化器里，**只在挂载时提交一次**。
 * 结算画面本来就意味着「本局分数已定格」，所以挂载即提交是可接受的语义；
 * 配合 records 的 roundId 幂等分支，StrictMode 双调用初始化器或组件重挂载
 * 都不会把局数计两次。
 *
 * 调用方仍需用 <AnimatePresence> 包住本组件以启用退场动画：
 *   <AnimatePresence>{over ? <ArcadeResult ... /> : null}</AnimatePresence>
 */
export function ArcadeResult({
  slug,
  score,
  mode,
  victory = false,
  title,
  subtitle,
  extraStats,
  actionLabel,
  onAction,
  secondaryLabel,
  onSecondary,
  cinematic,
  className,
}: {
  slug: ArcadeSlug
  /** 本局最终分数 */
  score: number
  /** 模式标识（写入 bestMode） */
  mode?: string
  victory?: boolean
  title?: string
  subtitle?: string
  /** 追加在「本局得分」之后的统计项（击杀 / 存活 / 波次…） */
  extraStats?: ResultStat[]
  actionLabel?: string
  onAction?: () => void
  secondaryLabel?: string
  onSecondary?: () => void
  cinematic?: boolean
  className?: string
}) {
  // 本局标识与结算一次成型；两者都放在初始化器里，保证同一次渲染里成对产生。
  const [roundId] = React.useState(() => newRoundId())
  const [result] = React.useState(() => submitRecord(slug, { score, mode, roundId }))

  const stats: ResultStat[] = [
    { label: "本局得分", value: formatScore(score) },
    ...(extraStats ?? []),
    { label: "历史最高", value: formatScore(result.record.best) },
  ]

  return (
    <ResultOverlay
      victory={victory}
      title={title}
      subtitle={subtitle}
      stats={stats}
      eyebrow={<BrandMark slug={slug} variant="inline" />}
      highlight={
        result.isNewBest ? (
          <span className="inline-flex items-center gap-1.5 border border-hud-accent/60 bg-hud-accent/15 px-3 py-1 font-mono-data text-[11px] uppercase tracking-[0.22em] text-hud-accent-bright backdrop-blur-sm">
            <span className="h-1 w-1 animate-pulse bg-hud-accent" />
            New Record
          </span>
        ) : null
      }
      actionLabel={actionLabel}
      onAction={onAction}
      secondaryLabel={secondaryLabel}
      onSecondary={onSecondary}
      cinematic={cinematic}
      className={className}
    />
  )
}
