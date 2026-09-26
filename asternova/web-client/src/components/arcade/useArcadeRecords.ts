"use client"

import * as React from "react"

import {
  getServerSnapshot,
  getSnapshot,
  parseRecords,
  subscribe,
  type ArcadeRecords,
} from "./records"

/**
 * 订阅街机记录。
 *
 * 用 useSyncExternalStore 而不是 useState + useEffect：
 * - 服务端快照固定为空串 → SSR 输出与首帧一致，不会产生 hydration mismatch
 *   （大厅卡片在未登录/无记录时不渲染「最高分」徽标，而非先渲染 0 再跳变）；
 * - 跨标签页写入会通过 storage 事件自动同步。
 */
export function useArcadeRecords(): ArcadeRecords {
  const raw = React.useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
  return React.useMemo(() => parseRecords(raw), [raw])
}

/** 便捷读取单个游戏的历史最高分；无记录返回 null（用于「不渲染徽标」而非渲染 0）。 */
export function useArcadeBest(slug: keyof ArcadeRecords["games"]): number | null {
  const records = useArcadeRecords()
  const best = records.games[slug]?.best
  return best && best > 0 ? best : null
}
