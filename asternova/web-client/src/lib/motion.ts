// AsterNova 动效 token（各页共享，避免重复定义 ease/spring）
// Usage: transition={{ ease: cinematicEase, duration: 0.7 }}
//        transition={springSnappy}

export const cinematicEase = [0.22, 1, 0.36, 1] as const

/** 通用弹簧：按钮 / 卡片交互 */
export const springSnappy = { type: "spring", stiffness: 420, damping: 26 } as const

/** 紧弹簧：列表项 / 小元素 */
export const springTight = { type: "spring", stiffness: 520, damping: 32 } as const

/** 区块入场：电影感（opacity + y） */
export const cinematicEnter = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: cinematicEase } },
} as const
