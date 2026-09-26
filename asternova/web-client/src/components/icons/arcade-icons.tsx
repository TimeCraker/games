/**
 * AsterNova 大厅图标系统（2026-09-26 自绘）
 *
 * 为什么不用 lucide / phosphor：
 *  1. 通用图标库是圆头圆角描边，一眼"SaaS"；游戏 HUD 需要等宽描边 + 斜切端点。
 *  2. 零依赖 = 零包体增量、零版本风险、可随时按品牌调整。
 *
 * 统一规格：viewBox 0 0 24 24 / fill none / stroke currentColor
 *          strokeWidth 1.5（可覆盖） / linecap square / linejoin miter
 * 取色：一律 currentColor，由父级 text-* 决定，禁止在组件内硬编码颜色。
 */

export type HudIconProps = {
  className?: string
  strokeWidth?: number
}

const base = (strokeWidth = 1.5) => ({
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth,
  strokeLinecap: "square" as const,
  strokeLinejoin: "miter" as const,
  "aria-hidden": true,
  focusable: false,
})

/* ---------- 游戏签名图标 ---------- */

/** Shoot Them All —— 弹射准星 */
export function HudTarget({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <circle cx="12" cy="12" r="7.25" />
      <circle cx="12" cy="12" r="2.25" />
      <path d="M12 1.75v3.5M12 18.75v3.5M1.75 12h3.5M18.75 12h3.5" />
    </svg>
  )
}

/** Let's Running —— 速度线 + 突进箭头 */
export function HudRunner({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <path d="M3 7h9M3 12h6M3 17h9" />
      <path d="M15 4.5L21 12l-6 7.5" />
    </svg>
  )
}

/** AsterNova Merge —— 二合一流向 */
export function HudMerge({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <circle cx="7.5" cy="5" r="2.75" />
      <circle cx="16.5" cy="5" r="2.75" />
      <path d="M7.5 7.75v1.75a4.5 4.5 0 0 0 9 0V7.75" />
      <circle cx="12" cy="18.5" r="3" />
    </svg>
  )
}

/** Nebula Survivor —— 俯视雷达 */
export function HudRadar({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <circle cx="12" cy="12" r="9.25" />
      <circle cx="12" cy="12" r="5.25" />
      <path d="M12 12l6.5-6.5" />
      <circle cx="14.75" cy="8.75" r="0.9" fill="currentColor" stroke="none" />
      <circle cx="9.25" cy="14.25" r="0.8" fill="currentColor" stroke="none" />
    </svg>
  )
}

/** 消消乐 —— 六边宝石（外框 + 内切面） */
export function HudHexGem({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <path d="M12 2.5 20.23 7.25v9.5L12 21.5 3.77 16.75v-9.5z" />
      <path d="M12 7.25 16.11 9.63v4.75L12 16.75 7.89 14.38V9.63z" />
    </svg>
  )
}

/* ---------- 结构 / 导航图标 ---------- */

/** 联机竞技 —— 交叉刀剑 */
export function HudSwords({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <path d="M3.5 3.5h2.75L18 15l-2.25 2.25L3.5 6.25z" />
      <path d="M20.5 3.5h-2.75L6 15l2.25 2.25L20.5 6.25z" />
      <path d="M16 16.5l4.5 4.5" />
      <path d="M8 16.5L3.5 21" />
    </svg>
  )
}

export function HudChevronRight({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <path d="M9 4.5l7.5 7.5L9 19.5" />
    </svg>
  )
}

/** 加载：8 段刻度环（配合 animate-spin 使用） */
export function HudSpinner({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <path d="M12 2.5v3.25M12 18.25v3.25" />
      <path d="M4.27 4.27l2.3 2.3M17.43 17.43l2.3 2.3" />
      <path d="M2.5 12h3.25M18.25 12h3.25" />
      <path d="M4.27 19.73l2.3-2.3M17.43 6.57l2.3-2.3" />
    </svg>
  )
}

export function HudGamepad({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <path d="M7.5 7.5h9a5 5 0 0 1 5 5v.75a3.6 3.6 0 0 1-6.7 1.85l-.55-.85H9.75l-.55.85A3.6 3.6 0 0 1 2.5 13.25v-.75a5 5 0 0 1 5-5z" />
      <path d="M7.25 10.75v3M5.75 12.25h3" />
      <circle cx="16.5" cy="11.25" r="0.95" fill="currentColor" stroke="none" />
      <circle cx="18.25" cy="13.25" r="0.95" fill="currentColor" stroke="none" />
    </svg>
  )
}

export function HudShield({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <path d="M12 2.5l8.25 3.1v6.15c0 5.05-3.5 8.7-8.25 10.75C7.25 20.45 3.75 16.8 3.75 11.75V5.6z" />
    </svg>
  )
}

export function HudBolt({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <path d="M13.75 2.5L4.5 13.75h6.25L10.25 21.5 19.5 10.25h-6.25z" />
    </svg>
  )
}

export function HudMoonStar({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <path d="M20.25 14.9A8.75 8.75 0 0 1 9.1 3.75a8.75 8.75 0 1 0 11.15 11.15z" />
      <path d="M17.75 2.5l.85 2.15 2.15.85-2.15.85-.85 2.15-.85-2.15-2.15-.85 2.15-.85z" />
    </svg>
  )
}

/** 复苏者 —— 治疗十字环 */
export function HudRevive({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <circle cx="12" cy="12" r="9.25" />
      <path d="M12 7.25v9.5M7.25 12h9.5" />
    </svg>
  )
}

export function HudIdCard({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <rect x="2.5" y="4.5" width="19" height="15" />
      <circle cx="8" cy="10.75" r="2.25" />
      <path d="M4.5 16.5c.9-1.75 2.2-2.6 3.5-2.6s2.6.85 3.5 2.6" />
      <path d="M14.75 9.75h4.25M14.75 12.75h4.25M14.75 15.75h2.75" />
    </svg>
  )
}

export function HudChip({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <rect x="6.5" y="6.5" width="11" height="11" />
      <rect x="10" y="10" width="4" height="4" />
      <path d="M9.5 2.5v4M14.5 2.5v4M9.5 17.5v4M14.5 17.5v4" />
      <path d="M2.5 9.5h4M2.5 14.5h4M17.5 9.5h4M17.5 14.5h4" />
    </svg>
  )
}

export function HudSpark({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <path d="M12 2.5c.7 4.4 3.1 6.8 7.5 7.5-4.4.7-6.8 3.1-7.5 7.5-.7-4.4-3.1-6.8-7.5-7.5 4.4-.7 6.8-3.1 7.5-7.5z" />
    </svg>
  )
}

export function HudUsers({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <circle cx="9" cy="8" r="3.25" />
      <path d="M2.5 20.5c0-3.6 2.9-6.5 6.5-6.5s6.5 2.9 6.5 6.5" />
      <path d="M16 5.3a3.25 3.25 0 0 1 0 5.4" />
      <path d="M17.5 14.6c2.4.95 4 3.2 4 5.9" />
    </svg>
  )
}

/** 信号强度 —— 在线人数 / 排位 */
export function HudSignal({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <path d="M3.5 20v-3.5M9 20v-7M14.5 20V8.5M20 20V4" />
    </svg>
  )
}

export function HudClose({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <path d="M5.5 5.5l13 13M18.5 5.5l-13 13" />
    </svg>
  )
}

export function HudLock({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <rect x="4.5" y="10.5" width="15" height="10" />
      <path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" />
    </svg>
  )
}

export function HudArrowLeft({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <path d="M20 12H4M10.5 5.5L4 12l6.5 6.5" />
    </svg>
  )
}

export function HudCheck({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <circle cx="12" cy="12" r="9.25" />
      <path d="M7.5 12.25l3 3 6-6.5" />
    </svg>
  )
}

export function HudInfo({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <circle cx="12" cy="12" r="9.25" />
      <path d="M12 11v6" />
      <circle cx="12" cy="7.75" r="1" fill="currentColor" stroke="none" />
    </svg>
  )
}

export function HudWarn({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <path d="M12 2.75L22.25 20.5H1.75z" />
      <path d="M12 9.5v4.5" />
      <circle cx="12" cy="17.25" r="1" fill="currentColor" stroke="none" />
    </svg>
  )
}

export function HudError({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className}>
      <circle cx="12" cy="12" r="9.25" />
      <path d="M8.5 8.5l7 7M15.5 8.5l-7 7" />
    </svg>
  )
}

/** 顶部装饰用：遥测刻度 */
export function HudTicks({ className, strokeWidth }: HudIconProps) {
  return (
    <svg {...base(strokeWidth)} className={className} preserveAspectRatio="none">
      <path d="M0 12h240" strokeOpacity="0.25" />
      <path d="M0 6v12M24 9v6M48 9v6M72 6v12M96 9v6M120 9v6M144 6v12M168 9v6M192 9v6M216 6v12M240 9v6" strokeOpacity="0.5" />
    </svg>
  )
}
