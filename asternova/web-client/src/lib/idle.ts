// onIdle —— requestIdleCallback 轻量包装（Safari 无此 API 时退化为短 setTimeout）
// 用途：把非关键初始化（WebGL 场景、埋点等）推迟到首帧渲染后的浏览器空闲期，
// 让出加载关键路径。性能基线 2026-10：game.asterforge.top 移动端 TBT 10.5s 的主因
// 之一是黑洞场景在 hydration 期同步启动。
export function onIdle(cb: () => void, timeoutMs = 2500): () => void {
  if (typeof window === "undefined") return () => {}
  const w = window as Window & {
    requestIdleCallback?: (cb: (deadline: IdleDeadline) => void, opts?: { timeout: number }) => number
    cancelIdleCallback?: (id: number) => void
  }
  if (typeof w.requestIdleCallback === "function") {
    const id = w.requestIdleCallback(() => cb(), { timeout: timeoutMs })
    return () => w.cancelIdleCallback?.(id)
  }
  const t = window.setTimeout(cb, Math.min(300, timeoutMs))
  return () => window.clearTimeout(t)
}
