"use client"

import * as React from "react"

/**
 * 自绘弹层的键盘可达性兜底（R1 ui-polish）：
 * - Esc 关闭（closeOnEsc=false 时仅做焦点陷阱，用于「必须显式确认」的弹层）
 * - Tab / Shift+Tab 焦点循环锁定在弹层内
 * - 打开时把焦点移入弹层（initialFocusRef 优先），关闭时归还焦点
 *
 * 用于游戏规则弹层、登录重置弹层等非 Radix 自绘 overlay；
 * open 时把返回的 ref 挂到弹层内容容器，并配 role="dialog" aria-modal="true"。
 */
export function useDialogA11y<T extends HTMLElement>({
  open,
  onClose,
  initialFocusRef,
  closeOnEsc = true,
}: {
  open: boolean
  onClose: () => void
  initialFocusRef?: React.RefObject<HTMLElement | null>
  closeOnEsc?: boolean
}) {
  const ref = React.useRef<T | null>(null)
  const onCloseRef = React.useRef(onClose)
  React.useEffect(() => {
    onCloseRef.current = onClose
  }, [onClose])

  React.useEffect(() => {
    if (!open) return
    const root = ref.current
    if (!root) return

    const prevActive = document.activeElement as HTMLElement | null
    const selector =
      'a[href], button:not([disabled]), input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    const focusables = () =>
      Array.from(root.querySelectorAll<HTMLElement>(selector)).filter(
        (el) => el.offsetParent !== null || el === document.activeElement,
      )
    ;(initialFocusRef?.current ?? focusables()[0] ?? root).focus()

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (!closeOnEsc) return
        e.preventDefault()
        e.stopPropagation()
        onCloseRef.current()
        return
      }
      if (e.key !== "Tab") return
      const list = focusables()
      if (list.length === 0) return
      const first = list[0]
      const last = list[list.length - 1]
      const active = document.activeElement
      if (e.shiftKey && (active === first || !root.contains(active))) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && (active === last || !root.contains(active))) {
        e.preventDefault()
        first.focus()
      }
    }
    document.addEventListener("keydown", onKey, true)
    return () => {
      document.removeEventListener("keydown", onKey, true)
      prevActive?.focus?.()
    }
  }, [open, closeOnEsc, initialFocusRef])

  return ref
}
