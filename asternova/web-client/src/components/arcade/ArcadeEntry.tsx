"use client"

import * as React from "react"

import { BrandMark } from "@/src/components/arcade/BrandMark"
import type { ArcadeSlug } from "@/src/components/arcade/brand"
import { StagePortal } from "@/src/components/game-shell/StagePortal"
import { useDialogA11y } from "@/src/hooks/useDialogA11y"
import { cn } from "@/lib/utils"

/**
 * 街机统一「开场 / 规则」弹层。
 *
 * 收编此前 merge / lets-running / nebula-survivor 三份手写实现：
 * 结构（标题 + 品牌行 + 规则列表 + 「下次不再显示」+ 确认按钮）、
 * 容器配方（rules.md §4）、键盘可达性（useDialogA11y）、portal（StagePortal）
 * 全部收敛到这里；**规则文案与内容一律由调用方以 children 传入，本组件不碰**。
 *
 * 刻意保留的差异（都在 props 上）：
 * - Esc 语义：给 onRequestClose 才可 Esc 关闭（merge / star-dash = 等同点确认按钮；
 *   nebula 的 briefing 不传 → closeOnEsc=false，必须显式点「开始任务」）。
 *   ⚠️ 与旧实现的唯一内部差异：旧代码对 briefing 是「closeOnEsc=true + onClose 空转」
 *   （Esc 被 preventDefault 吃掉），此处是 closeOnEsc=false（Esc 继续冒泡）。
 *   nebula 自身的 Esc/P 处理器此时读 rulesOpenRef 判定 briefing 后直接 return，
 *   故对外可观察行为一致。
 * - localStorage 读写仍留在各游戏内（本组件只做受控展示，不碰 storage）。
 * - 三个游戏的 skip key / 文案 / 按钮配色 / 层级 / 是否居中，全部由 props 给定。
 */

/** 玻璃面板配方（rules.md §4）：移动端底部抽屉，桌面全圆角 */
const PANEL_DRAWER =
  "max-h-[min(88dvh,calc(100dvh-env(safe-area-inset-top)-env(safe-area-inset-bottom)-1.5rem))] w-full max-w-[420px] overflow-y-auto overscroll-contain rounded-t-[1.75rem] border border-glass-border border-b-0 bg-glass-bg p-4 shadow-lg backdrop-blur-glass-lg sm:rounded-[2rem] sm:border-b sm:p-6"
/** 居中式变体（star-dash 原样）：全圆角，高度交给内容 */
const PANEL_CENTERED =
  "w-full max-w-[420px] rounded-[2rem] border border-glass-border bg-glass-bg p-6 shadow-lg backdrop-blur-glass-lg"

const OVERLAY_DRAWER = "fixed inset-0 flex items-end justify-center backdrop-blur-md sm:items-center"
const OVERLAY_CENTERED = "fixed inset-0 flex items-center justify-center backdrop-blur-md"

/** 复选框本体：三处逐字节相同，收进来做单一真源 */
const SKIP_CHECKBOX =
  "h-4 w-4 rounded-md border-white/30 bg-white/10 text-hud-accent focus:ring-hud-accent/50"
const SKIP_ROW_BASE =
  "flex cursor-pointer items-center gap-3 rounded-2xl border border-white/[0.08] bg-white/[0.04] transition hover:bg-white/[0.06]"
/** merge / star-dash 的行内距与字号（nebula 由调用方整体覆盖） */
const SKIP_ROW_DEFAULT = "mt-5 px-4 py-3 text-[13px] text-white/70"
const SKIP_LABEL_DEFAULT = "下次不再显示规则（本机记住）"

/** 确认按钮默认配方 = merge 原样（star-dash 传白底、nebula 传自己的圆角与投影） */
const CONFIRM_DEFAULT =
  "mt-5 w-full rounded-2xl bg-gradient-to-r from-amber-400 via-amber-500 to-amber-600 py-3.5 text-[15px] font-semibold text-gray-950 shadow-lg shadow-amber-500/20 transition hover:brightness-105 active:scale-[0.99]"

const TITLE_DEFAULT = "text-center text-xl font-semibold tracking-tight text-white"
const SUBTITLE_DEFAULT = "mt-1 flex items-center justify-center"

/** 遮罩安全区内距（merge / nebula 原样逐字节搬入） */
const SAFE_AREA_STYLE: React.CSSProperties = {
  paddingLeft: "max(0.75rem, env(safe-area-inset-left, 0px))",
  paddingRight: "max(0.75rem, env(safe-area-inset-right, 0px))",
  paddingBottom: "max(0.75rem, env(safe-area-inset-bottom, 0px))",
  paddingTop: "max(0.5rem, env(safe-area-inset-top, 0px))",
}

export type ArcadeEntrySkipRules = {
  /** 受控勾选态（初值仍由各游戏的 useState 持有） */
  checked: boolean
  onChange: (checked: boolean) => void
  /** 复选框文案；默认「下次不再显示规则（本机记住）」 */
  label?: string
  /** 整行附加类（整体覆盖默认行内距 / 字号；基础玻璃行样式保留） */
  className?: string
}

export function ArcadeEntry({
  slug,
  titleId,
  title = "怎么玩",
  titleClassName = TITLE_DEFAULT,
  subtitle,
  subtitleClassName = SUBTITLE_DEFAULT,
  /** 无显式 subtitle 时，是否自动渲染 BrandMark inline 品牌行（merge / star-dash） */
  brandInline = true,
  /** 标题上方的附加内容（nebula 的「Briefing」眉标 + 「已暂停」徽标） */
  eyebrow,
  /** 面板内最先生成的装饰层（nebula 的 PanelCorners） */
  panelOverlay,
  children,
  label,
  onConfirm,
  /** 提供则 Esc 可关（调用它）；不提供则只做焦点陷阱 */
  onRequestClose,
  initialFocusRef,
  skipRules,
  variant = "drawer",
  overlayZClassName = "z-50",
  overlayTint = "bg-black/55",
  overlayPadding,
  safeArea = false,
  overlayStyle,
  overlayClassName,
  panelClassName,
  confirmClassName,
  footer,
}: {
  /** 品牌行取名的单一真源 */
  slug: ArcadeSlug
  /** aria-labelledby 指向的标题 id（保持各游戏既有 id 不变） */
  titleId: string
  title?: React.ReactNode
  titleClassName?: string
  subtitle?: React.ReactNode
  subtitleClassName?: string
  brandInline?: boolean
  eyebrow?: React.ReactNode
  panelOverlay?: React.ReactNode
  /** 规则列表：内容与排版由调用方传入，本组件不碰 */
  children: React.ReactNode
  /** 确认按钮文案 */
  label: string
  onConfirm: () => void
  onRequestClose?: () => void
  initialFocusRef?: React.RefObject<HTMLElement | null>
  skipRules?: ArcadeEntrySkipRules
  variant?: "drawer" | "centered"
  overlayZClassName?: string
  overlayTint?: string
  /** 覆盖默认的 sm:p-4（drawer）/ p-4（centered） */
  overlayPadding?: string
  safeArea?: boolean
  overlayStyle?: React.CSSProperties
  overlayClassName?: string
  panelClassName?: string
  /**
   * 确认按钮类的**整体覆盖**（默认 = merge 配方）。
   * 刻意不走 cn/twMerge：tailwind-merge 会把 shadow-lg 与 shadow-amber-500/20
   * 判成同组而丢掉前者（实测），会让按钮阴影直接消失。
   */
  confirmClassName?: string
  footer?: React.ReactNode
}) {
  const closeFromKeyboard = React.useCallback(() => {
    onRequestClose?.()
  }, [onRequestClose])

  // Esc 语义由「是否给了 onRequestClose」决定；焦点陷阱 / 初始焦点 / 还焦一律保留。
  const dialogRef = useDialogA11y<HTMLDivElement>({
    open: true,
    onClose: closeFromKeyboard,
    closeOnEsc: Boolean(onRequestClose),
    initialFocusRef,
  })

  const isCentered = variant === "centered"
  const overlayClass = cn(
    isCentered ? OVERLAY_CENTERED : OVERLAY_DRAWER,
    overlayPadding ?? (isCentered ? "p-4" : "sm:p-4"),
    overlayTint,
    overlayZClassName,
    overlayClassName,
  )
  const panelClass = cn(isCentered ? PANEL_CENTERED : PANEL_DRAWER, panelClassName)

  const brandRow =
    subtitle != null ? (
      <p className={subtitleClassName}>{subtitle}</p>
    ) : brandInline ? (
      <p className={subtitleClassName}>
        <BrandMark slug={slug} variant="inline" className="text-[13px]" />
      </p>
    ) : null

  return (
    <StagePortal>
      <div
        ref={dialogRef}
        className={overlayClass}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        style={safeArea ? { ...SAFE_AREA_STYLE, ...overlayStyle } : overlayStyle}
      >
        <div className={panelClass}>
          {panelOverlay}
          {eyebrow}
          <h2 id={titleId} className={titleClassName}>
            {title}
          </h2>
          {brandRow}
          {children}
          {skipRules ? (
            <label className={cn(SKIP_ROW_BASE, skipRules.className ?? SKIP_ROW_DEFAULT)}>
              <input
                type="checkbox"
                checked={skipRules.checked}
                onChange={(e) => skipRules.onChange(e.target.checked)}
                className={SKIP_CHECKBOX}
              />
              {skipRules.label ?? SKIP_LABEL_DEFAULT}
            </label>
          ) : null}
          <button type="button" onClick={onConfirm} className={confirmClassName ?? CONFIRM_DEFAULT}>
            {label}
          </button>
          {footer}
        </div>
      </div>
    </StagePortal>
  )
}
