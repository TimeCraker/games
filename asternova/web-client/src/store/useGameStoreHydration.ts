"use client"

import * as React from "react"

import { useGameStore } from "@/src/store/useGameStore"

/**
 * Zustand persist 从 localStorage 异步恢复；在 rehydrate 完成前 token 等仍为初始空值。
 * 依赖 token 的路由守卫须等此项为 true 后再判断，否则会误踢回登录页。
 *
 * 注意：不得在 SSR / 首帧同步读取 `useGameStore.persist`（预渲染环境下可能不存在）。
 */
export function useGameStoreRehydrated(): boolean {
  const [rehydrated, setRehydrated] = React.useState(false)

  React.useEffect(() => {
    const p = useGameStore.persist
    if (!p) {
      setRehydrated(true)
      return
    }
    if (p.hasHydrated()) {
      setRehydrated(true)
      return
    }
    return p.onFinishHydration(() => {
      setRehydrated(true)
    })
  }, [])

  return rehydrated
}
