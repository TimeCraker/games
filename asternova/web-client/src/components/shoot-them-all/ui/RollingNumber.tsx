"use client"

import * as React from "react"

import { cn } from "@/lib/utils"

/**
 * 等宽数字滚动（art bible §5 #14）：变化位数字纵向滚动，150ms `--ease-instrument`。
 *
 * 实现要点：
 * - 每个数位是一列 0–9，靠 `transform: translateY` 落位，只动 transform（§5 总则）；
 * - **列按「从右数的位次」key 住**（R6 修：原先按「总位数-列序」key，分数跨千位时
 *   整列重挂、大跳分瞬跳）：位数增减只增删高位列，既有列平滑滚到新数字；
 * - 千分位逗号等非数位字符静态渲染，不参与滚动；
 * - 新增的最高位列挂载即落位（无过渡，符合「进位」的视觉预期）。
 */

const DIGIT_COUNT = 10

function DigitColumn({ digit, style }: { digit: number; style?: React.CSSProperties }) {
  return (
    <span
      className="relative inline-block overflow-hidden align-baseline"
      style={{ height: "1em", width: "0.62em", ...style }}
      aria-hidden="true"
    >
      <span
        className="absolute left-0 top-0 flex flex-col transition-transform duration-150"
        style={{
          transform: `translateY(${-digit * 100 / DIGIT_COUNT}%)`,
          transitionTimingFunction: "var(--ease-instrument)",
          height: `${DIGIT_COUNT * 100}%`,
        }}
      >
        {Array.from({ length: DIGIT_COUNT }, (_, n) => (
          <span key={n} className="flex h-[10%] items-center justify-center leading-none">
            {n}
          </span>
        ))}
      </span>
    </span>
  )
}

export function RollingNumber({
  value,
  className,
  label,
}: {
  value: number
  className?: string
  /** 无障碍朗读用的纯文本（滚动列本身 aria-hidden） */
  label?: string
}) {
  const n = Number.isFinite(value) ? Math.max(0, Math.floor(value)) : 0
  const digits = String(n)

  // 千分位分组（从右每 3 位一组）
  const groups = React.useMemo(() => {
    const gs: string[] = []
    for (let end = digits.length; end > 0; end -= 3) {
      gs.unshift(digits.slice(Math.max(0, end - 3), end))
    }
    return gs
  }, [digits])

  return (
    <span className={cn("inline-flex items-baseline tabular-nums", className)} aria-label={label ?? n.toLocaleString("en-US")}>
      {groups.map((g, gi) => (
        <React.Fragment key={`g${groups.length - gi}`}>
          {gi > 0 ? (
            <span aria-hidden="true" className="inline-block text-center">
              ,
            </span>
          ) : null}
          {g.split("").map((ch, ci) => {
            // 最左组可能不足 3 位；其余组恒为 3 位，从右侧反推起点
            const offset = gi === 0 ? 0 : digits.length - 3 * (groups.length - gi)
            const posFromRight = digits.length - 1 - (offset + ci)
            return ch >= "0" && ch <= "9" ? (
              <DigitColumn key={`d${posFromRight}`} digit={ch.charCodeAt(0) - 48} />
            ) : (
              <span key={`d${posFromRight}`} aria-hidden="true" className="inline-block text-center">
                {ch}
              </span>
            )
          })}
        </React.Fragment>
      ))}
    </span>
  )
}
