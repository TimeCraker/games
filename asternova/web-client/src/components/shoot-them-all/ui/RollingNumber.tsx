"use client"

import * as React from "react"

import { cn } from "@/lib/utils"

/**
 * 等宽数字滚动（art bible §5 #14）：变化位数字纵向滚动 1 格，150ms `--ease-instrument`。
 *
 * 实现要点：
 * - 每个数位是一列 0–9，靠 `transform: translateY` 落位，只动 transform（§5 总则）；
 * - 列按位次 key 住，DOM 增删只随位数变化发生，绝不逐帧创建（§5 #14「缓存 DOM」）；
 * - 千分位逗号等非数位字符静态渲染，不参与滚动。
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
  const text = React.useMemo(() => {
    const n = Number.isFinite(value) ? Math.max(0, Math.floor(value)) : 0
    return n.toLocaleString("en-US")
  }, [value])

  return (
    <span className={cn("inline-flex items-baseline tabular-nums", className)} aria-label={label ?? text}>
      {text.split("").map((ch, i) =>
        ch >= "0" && ch <= "9" ? (
          <DigitColumn key={`${text.length}-${i}`} digit={ch.charCodeAt(0) - 48} />
        ) : (
          <span key={`${text.length}-${i}`} aria-hidden="true" className="inline-block text-center">
            {ch}
          </span>
        ),
      )}
    </span>
  )
}
