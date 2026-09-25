"use client"

import * as React from "react"
import { createPortal } from "react-dom"

/**
 * 把弹层 / 悬浮 chrome 渲染到 document.body，脱离 ScaleFitGameStage 的 transform 缩放。
 * 依据 rules §3：交互控件禁止放进 transform: scale() 容器（否则手机端被等比缩小到 <24px）。
 *
 * SSR 安全：首帧内联渲染（与预渲染 HTML 结构一致，避免 hydration mismatch），
 * effect 后切到 portal；初始打开的弹层会重放一次入场动画（约一帧，不可感知）。
 */
export function StagePortal({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = React.useState(false)
  React.useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    // 首帧结构与 SSR 一致，但隐藏避免闪烁
    return <div style={{ display: "none" }} aria-hidden="true">{children}</div>
  }
  return createPortal(children, document.body)
}
