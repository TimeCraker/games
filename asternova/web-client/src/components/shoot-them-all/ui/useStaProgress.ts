"use client"

import * as React from "react"

import {
  getServerSnapshot,
  getSnapshot,
  parseProgress,
  subscribe,
  type StaProgress,
} from "./staProgress"

/**
 * 订阅本作关卡进度（useSyncExternalStore，快照用原始串保证引用稳定）。
 * 服务端快照恒为空串 → 首帧不水合错位，挂载后再读真实进度。
 */
export function useStaProgress(): StaProgress {
  const raw = React.useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
  return React.useMemo(() => parseProgress(raw), [raw])
}
