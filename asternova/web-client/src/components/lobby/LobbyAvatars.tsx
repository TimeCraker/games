"use client"

import * as React from "react"
import { AnimatePresence, motion } from "framer-motion"
import { useDialogA11y } from "@/src/hooks/useDialogA11y"

export const LOBBY_AVATAR_STORAGE_KEY = "asternova-lobby-avatar-id"

export const LOBBY_AVATAR_IDS = [
  "avatar-1",
  "avatar-2",
  "avatar-3",
  "avatar-4",
  "avatar-5",
  "avatar-6",
  "avatar-7",
  "avatar-8",
  "avatar-9",
  "avatar-10",
] as const

export type LobbyAvatarId = (typeof LOBBY_AVATAR_IDS)[number]

/* ============================================================================
   2026-09-27 重做：原 10 个头像是「卡通圆脸」且色板为 #A855F7 / #F472B6 /
   #EC4899 / #2DD4BF 等紫粉玫青 —— 正是从主题中清除的色系，且画风与工业化
   琥珀主题冲突。改为「星图徽章」：深色圆盘 + 琥珀星点 + 细微连线，
   复用大厅已有的星图设计语言，10 个星座形状辨识度天然不同。

   每个头像 = 一组星点坐标 + 连线索引，数据驱动，便于增删与微调。
   ============================================================================ */

type Constellation = {
  id: LobbyAvatarId
  /** 中文名（弹层可读） */
  name: string
  /** 星点 [x, y, r]，坐标系 48×48，四周留 ~6px 安全边距 */
  stars: Array<[number, number, number]>
  /** 连线（星点索引对） */
  lines: Array<[number, number]>
}

export const LOBBY_CONSTELLATIONS: Constellation[] = [
  {
    id: "avatar-1",
    name: "猎户座",
    stars: [[17, 11, 1.5], [31, 13, 1.2], [20.5, 24, 1.1], [24, 25, 1.1], [27.5, 26, 1.1], [18, 37, 1.3], [31, 36, 1.5]],
    lines: [[0, 1], [0, 2], [1, 4], [2, 3], [3, 4], [2, 5], [4, 6], [5, 6]],
  },
  {
    id: "avatar-2",
    name: "北斗七星",
    stars: [[7, 31, 1.1], [13, 27, 1.1], [19, 25, 1.2], [25, 22, 1.1], [32, 19, 1.2], [35, 27, 1.1], [28, 30, 1.1]],
    lines: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 3]],
  },
  {
    id: "avatar-3",
    name: "仙后座",
    stars: [[7, 15, 1.2], [16, 31, 1.1], [24, 17, 1.3], [32, 32, 1.1], [41, 14, 1.2]],
    lines: [[0, 1], [1, 2], [2, 3], [3, 4]],
  },
  {
    id: "avatar-4",
    name: "天鹅座",
    stars: [[24, 7, 1.5], [24, 24, 1.2], [24, 41, 1.1], [10, 22, 1.1], [38, 24, 1.1]],
    lines: [[0, 1], [1, 2], [3, 1], [1, 4]],
  },
  {
    id: "avatar-5",
    name: "天琴座",
    stars: [[18, 8, 1.7], [14, 20, 1.1], [25, 22, 1.1], [27, 33, 1.0], [16, 31, 1.0]],
    lines: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 1]],
  },
  {
    id: "avatar-6",
    name: "天蝎座",
    stars: [[10, 11, 1.1], [14, 15, 1.0], [19, 17, 1.2], [21, 23, 1.1], [22, 30, 1.0], [27, 36, 1.1], [34, 38, 1.2], [40, 33, 1.3]],
    lines: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7]],
  },
  {
    id: "avatar-7",
    name: "狮子座",
    stars: [[11, 13, 1.1], [15, 9, 1.2], [20, 12, 1.0], [21, 18, 1.1], [17, 23, 1.0], [30, 17, 1.2], [38, 24, 1.1], [29, 33, 1.0]],
    lines: [[0, 1], [1, 2], [2, 3], [3, 4], [3, 5], [5, 6], [6, 7], [7, 4]],
  },
  {
    id: "avatar-8",
    name: "飞马座",
    stars: [[11, 13, 1.3], [33, 11, 1.2], [36, 31, 1.1], [14, 33, 1.1], [41, 21, 1.0]],
    lines: [[0, 1], [1, 2], [2, 3], [3, 0], [1, 4]],
  },
  {
    id: "avatar-9",
    name: "双子座",
    stars: [[13, 9, 1.4], [14, 20, 1.1], [16, 31, 1.0], [18, 40, 1.0], [29, 10, 1.5], [30, 21, 1.1], [31, 32, 1.0], [32, 41, 1.0]],
    lines: [[0, 1], [1, 2], [2, 3], [4, 5], [5, 6], [6, 7], [1, 5], [2, 6]],
  },
  {
    id: "avatar-10",
    name: "御夫座",
    stars: [[13, 11, 1.5], [32, 12, 1.1], [39, 26, 1.0], [24, 40, 1.0], [10, 27, 1.1]],
    lines: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0]],
  },
]

function readStoredAvatarId(): LobbyAvatarId | null {
  if (typeof window === "undefined") return null
  try {
    const v = localStorage.getItem(LOBBY_AVATAR_STORAGE_KEY)
    if (v && LOBBY_AVATAR_IDS.includes(v as LobbyAvatarId)) return v as LobbyAvatarId
  } catch {
    /* ignore */
  }
  return null
}

export function writeStoredAvatarId(id: LobbyAvatarId) {
  try {
    localStorage.setItem(LOBBY_AVATAR_STORAGE_KEY, id)
  } catch {
    /* ignore */
  }
}

export function pickRandomAvatarId(): LobbyAvatarId {
  const i = Math.floor(Math.random() * LOBBY_AVATAR_IDS.length)
  return LOBBY_AVATAR_IDS[i]!
}

/** 首次进入大厅：无记录则随机并写入 */
export function ensureLobbyAvatarId(): LobbyAvatarId {
  const existing = readStoredAvatarId()
  if (existing) return existing
  const id = pickRandomAvatarId()
  writeStoredAvatarId(id)
  return id
}

/** 星图徽章：48×48 视口，深色圆盘 + 琥珀星点 + 细微连线 */
export function LobbyPresetAvatar({
  id,
  className = "",
}: {
  id: LobbyAvatarId
  className?: string
}) {
  const c = LOBBY_CONSTELLATIONS.find((x) => x.id === id) ?? LOBBY_CONSTELLATIONS[0]
  return (
    <svg className={className} viewBox="0 0 48 48" aria-hidden focusable="false">
      <circle cx="24" cy="24" r="22.5" className="fill-ink-800" />
      <circle cx="24" cy="24" r="22.5" fill="none" strokeWidth="1" className="stroke-hud-accent/25" />
      <g fill="none" strokeWidth="0.9" strokeLinecap="square" className="stroke-hud-accent/45">
        {c.lines.map(([a, b], i) => {
          const A = c.stars[a]
          const B = c.stars[b]
          if (!A || !B) return null
          return <line key={i} x1={A[0]} y1={A[1]} x2={B[0]} y2={B[1]} />
        })}
      </g>
      <g className="fill-hud-accent-bright">
        {c.stars.map(([x, y, r], i) => (
          <circle key={i} cx={x} cy={y} r={r} />
        ))}
      </g>
    </svg>
  )
}

export function useLobbyAvatar() {
  const [avatarId, setAvatarIdState] = React.useState<LobbyAvatarId>("avatar-1")
  const [pickerOpen, setPickerOpen] = React.useState(false)

  React.useLayoutEffect(() => {
    setAvatarIdState(ensureLobbyAvatarId())
  }, [])

  const setAvatarId = React.useCallback((id: LobbyAvatarId) => {
    writeStoredAvatarId(id)
    setAvatarIdState(id)
    setPickerOpen(false)
  }, [])

  return { avatarId, setAvatarId, pickerOpen, setPickerOpen }
}

export function LobbyAvatarPickerModal({
  open,
  onClose,
  currentId,
  onSelect,
}: {
  open: boolean
  onClose: () => void
  currentId: LobbyAvatarId
  onSelect: (id: LobbyAvatarId) => void
}) {
  // Esc 关闭 + Tab 焦点陷阱（与登录重置弹层同款 useDialogA11y）
  const dialogRef = useDialogA11y<HTMLDivElement>({ open, onClose })
  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          className="fixed inset-0 z-[300] flex items-end justify-center p-4 sm:items-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <button
            type="button"
            className="absolute inset-0 bg-ink-1000/70 backdrop-blur-sm"
            aria-label="关闭"
            onClick={onClose}
          />
          <motion.div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="lobby-avatar-picker-title"
            initial={{ opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.98 }}
            transition={{ type: "spring", stiffness: 380, damping: 28 }}
            className="hud-chamfer relative z-[1] w-full max-w-[368px] overflow-hidden border border-hud-line bg-ink-800/96 p-5 shadow-[0_24px_80px_rgba(0,0,0,0.7),inset_0_1px_0_rgba(255,255,255,0.05)] backdrop-blur-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h2
              id="lobby-avatar-picker-title"
              className="text-center text-[15px] font-semibold tracking-[-0.01em] text-hud-paper"
            >
              选择星图徽章
            </h2>
            <p className="mt-1 text-center text-[12px] text-hud-text-dim">
              以星座为记 · 仅保存在本机
            </p>

            <div className="mt-5 grid grid-cols-5 gap-2.5">
              {LOBBY_CONSTELLATIONS.map((c) => {
                const active = c.id === currentId
                return (
                  <motion.button
                    key={c.id}
                    type="button"
                    onClick={() => onSelect(c.id)}
                    whileHover={{ scale: 1.06 }}
                    whileTap={{ scale: 0.94 }}
                    title={c.name}
                    aria-label={c.name}
                    aria-pressed={active}
                    className={[
                      "flex aspect-square items-center justify-center border p-1 transition-colors duration-150 focus-visible:outline-none",
                      active
                        ? "border-hud-accent/70 bg-hud-accent/12 shadow-[var(--glow-accent)]"
                        : "border-hud-line bg-ink-900/60 hover:border-hud-accent/40 hover:bg-hud-accent/[0.06]",
                    ].join(" ")}
                  >
                    <LobbyPresetAvatar id={c.id} className="h-full w-full" />
                  </motion.button>
                )
              })}
            </div>

            <p className="mt-3 text-center font-mono-data text-[11px] tracking-[0.06em] text-hud-text-faint">
              {LOBBY_CONSTELLATIONS.find((c) => c.id === currentId)?.name ?? ""}
            </p>

            <button
              type="button"
              onClick={onClose}
              className="mt-4 w-full border border-hud-accent/50 bg-hud-accent/12 py-2.5 text-[13px] font-medium text-hud-accent-bright transition-colors duration-150 hover:border-hud-accent hover:bg-hud-accent hover:text-ink-1000 focus-visible:outline-none focus-visible:border-hud-accent"
            >
              完成
            </button>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}
