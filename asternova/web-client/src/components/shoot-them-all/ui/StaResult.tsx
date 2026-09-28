"use client"

import * as React from "react"

import { ArcadeResult } from "@/src/components/arcade/ArcadeResult"

/**
 * 结算 · ResultOverlay / Morphing Modal（art bible §4.5）。
 *
 * 严格走街机组装层 ArcadeResult（它封装 BrandMark eyebrow、本局得分 + 历史最高、
 * NEW RECORD 标记，并内部调用 ResultOverlay + records.submitRecord），
 * 本作**不自造结算浮层**。调用方用 <AnimatePresence> 包裹。
 *
 * 传参按 §4.5 写死：
 *   slug="shoot-them-all" · mode=`lv${关号}` · cinematic=true · slogan 默认
 *   victory = score >= 目标分 · title 走默认 VICTORY / SIGNAL LOST
 *   过关 subtitle=`三星通关 · 剩余 n 球`（按实绩写星与剩余数），action=下一关
 *   失败 subtitle=`差 X 分，再来一发`，action=重试本关
 *   secondary 一律 返回大厅
 *   extraStats=[剩余球, 星级, 连击峰值]
 *
 * 星级图形本体的爆闪在画布层（渲染层），Modal 内只负责落定读数。
 */

const STAR_CN = ["", "一星", "二星", "三星"]

export type StaResultData = {
  levelId: number
  score: number
  targetScore: number
  stars: number
  ballsLeft: number
  bestCombo: number
}

export function StaResult({
  data,
  isLastLevel,
  onNext,
  onRetry,
  onExit,
}: {
  data: StaResultData
  isLastLevel: boolean
  /** 过关 → 下一关（末关则回到第 1 关重开一圈） */
  onNext: () => void
  /** 失败 → 重试本关 */
  onRetry: () => void
  onExit: () => void
}) {
  const victory = data.score >= data.targetScore
  const stars = Math.max(0, Math.min(3, data.stars))

  const subtitle = victory
    ? `${STAR_CN[stars] || ""}通关 · 剩余 ${data.ballsLeft} 球`
    : `差 ${Math.max(0, data.targetScore - data.score).toLocaleString("en-US")} 分，再来一发`

  const starText = "★".repeat(stars) + "☆".repeat(3 - stars)

  return (
    <ArcadeResult
      slug="shoot-them-all"
      score={data.score}
      mode={`lv${data.levelId}`}
      victory={victory}
      subtitle={subtitle}
      extraStats={[
        { label: "剩余球", value: data.ballsLeft },
        { label: "星级", value: starText },
        { label: "连击峰值", value: `×${Math.max(1, data.bestCombo)}` },
      ]}
      actionLabel={victory ? (isLastLevel ? "再战一圈" : "下一关") : "重试本关"}
      onAction={victory ? onNext : onRetry}
      secondaryLabel="返回选关"
      onSecondary={onExit}
      cinematic
    />
  )
}
