"use client"

import * as React from "react"

/**
 * 自绘弹层的键盘可达性兜底（R1 ui-polish，R6 改版为 portal 免疫）：
 * - Esc 关闭（closeOnEsc=false 时仅做焦点陷阱，用于「必须显式确认」的弹层）
 * - Tab / Shift+Tab 焦点循环锁定在弹层内
 * - 打开时把焦点移入弹层（initialFocusRef 优先），关闭时归还焦点
 *
 * R6 修订：弹层可能经 StagePortal 从临时容器延迟搬运到 document.body
 * （首帧 display:none → focus() 失败；DOM 移动前后 root 引用可能失效）。
 * 现在每次按键都从 ref 实时解析 root、只对已连接且可见的节点计算 focusables，
 * 并对「首帧不可聚焦」场景做有限次重试聚焦（60ms × 20），保证 portal 迁移后陷阱依旧生效。
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
    const timers = new Set<number>()
    const selector =
      'a[href], button:not([disabled]), input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    const rootEl = () => ref.current
    const focusables = () => {
      const r = rootEl()
      if (!r || !r.isConnected) return [] as HTMLElement[]
      return Array.from(r.querySelectorAll<HTMLElement>(selector)).filter(
        (el) => el.offsetParent !== null || el === document.activeElement,
      )
    }
    const focusFirst = () => {
      const list = focusables()
      const target = (initialFocusRef?.current ?? list[0] ?? rootEl()) as HTMLElement | undefined
      target?.focus?.()
    }
    const prevActive = document.activeElement as HTMLElement | null
    // 立即尝试聚焦；若根尚未可见（临时容器 / display:none 首帧）则周期重试直到命中
    focusFirst()
    let retries = 0
    const retrySchedule = () => {
      const id = window.setTimeout(() => {
        timers.delete(id)
        const r = rootEl()
        if (!r || !r.isConnected) return // 已卸载则停
        if (focusables().length > 0 && !r.contains(document.activeElement)) {
          focusFirst()
          return
        }
        if (focusables().length === 0 && retries++ < 20) retrySchedule()
      }, 60)
      timers.add(id)
    }
    retrySchedule()

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (!closeOnEsc) return
        e.preventDefault()
        e.stopPropagation()
        onCloseRef.current()
        return
      }
      if (e.key !== "Tab") return
      const r = rootEl()
      const list = focusables()
      if (!r || list.length === 0) return
      const first = list[0]
      const last = list[list.length - 1]
      const active = document.activeElement
      if (e.shiftKey && (active === first || !r.contains(active))) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && (active === last || !r.contains(active))) {
        e.preventDefault()
        first.focus()
      }
    }
    document.addEventListener("keydown", onKey, true)
    return () => {
      document.removeEventListener("keydown", onKey, true)
      for (const id of timers) window.clearTimeout(id)
      timers.clear()
      prevActive?.focus?.()
    }
  }, [open, closeOnEsc, initialFocusRef])

  return ref
}
