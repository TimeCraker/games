// AsterNova 动效 token（各页共享，避免重复定义 ease/spring）
// Usage: transition={{ ease: cinematicEase, duration: 0.7 }}
//        transition={springSnappy}

export const cinematicEase = [0.22, 1, 0.36, 1] as const

/** 微交互曲线（globals.css --ease-instrument 的 JS 侧镜像，HUD 组件大量内联） */
export const easeInstrument = [0.32, 0.72, 0, 1] as const

/** 列表交错入场延迟：每项 +30ms（STYLE.md §5.4 节奏），base 用于让位更早的元素 */
export function staggerDelay(index: number, step = 0.03, base = 0): number {
  return base + index * step
}

/** 通用弹簧：按钮 / 卡片交互 */
export const springSnappy = { type: "spring", stiffness: 420, damping: 26 } as const

/** 紧弹簧：列表项 / 小元素 */
export const springTight = { type: "spring", stiffness: 520, damping: 32 } as const

/** 区块入场：电影感（opacity + y） */
export const cinematicEnter = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: cinematicEase } },
} as const
