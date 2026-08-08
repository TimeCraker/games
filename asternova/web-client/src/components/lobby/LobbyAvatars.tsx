"use client"

import * as React from "react"
import { AnimatePresence, motion } from "framer-motion"

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

/** 简约卡通圆脸，48×48 视口 */
export function LobbyPresetAvatar({
  id,
  className = "",
}: {
  id: LobbyAvatarId
  className?: string
}) {
  const common = { className: `block ${className}`, viewBox: "0 0 48 48", fill: "none", "aria-hidden": true as const }

  switch (id) {
    case "avatar-1":
      return (
        <svg {...common}>
          <circle cx="24" cy="24" r="20" fill="#FECDD3" stroke="#FB7185" strokeWidth="1.5" />
          <circle cx="17" cy="21" r="2.2" fill="#1f2937" />
          <circle cx="31" cy="21" r="2.2" fill="#1f2937" />
          <path d="M18 30c2.5 3 9.5 3 12 0" stroke="#1f2937" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      )
    case "avatar-2":
      return (
        <svg {...common}>
          <circle cx="24" cy="24" r="20" fill="#A7F3D0" stroke="#34D399" strokeWidth="1.5" />
          <path d="M15 20l3 2-3 2M30 20l3 2-3 2" stroke="#065F46" strokeWidth="1.4" strokeLinecap="round" />
          <circle cx="24" cy="31" r="2" fill="#059669" />
        </svg>
      )
    case "avatar-3":
      return (
        <svg {...common}>
          <circle cx="24" cy="24" r="20" fill="#DDD6FE" stroke="#A78BFA" strokeWidth="1.5" />
          <path d="M16 22h6M26 22h6" stroke="#5B21B6" strokeWidth="2" strokeLinecap="round" />
          <path d="M18 30h12" stroke="#5B21B6" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      )
    case "avatar-4":
      return (
        <svg {...common}>
          <circle cx="24" cy="24" r="20" fill="#FEF08A" stroke="#EAB308" strokeWidth="1.5" />
          <circle cx="17" cy="21" r="2" fill="#1f2937" />
          <circle cx="31" cy="21" r="2" fill="#1f2937" />
          <ellipse cx="17" cy="26" rx="2" ry="1.2" fill="#F472B6" opacity="0.7" />
          <ellipse cx="31" cy="26" rx="2" ry="1.2" fill="#F472B6" opacity="0.7" />
          <path d="M20 31c1.2 1.8 6.8 1.8 8 0" stroke="#92400E" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      )
    case "avatar-5":
      return (
        <svg {...common}>
          <circle cx="24" cy="24" r="20" fill="#BAE6FD" stroke="#38BDF8" strokeWidth="1.5" />
          <circle cx="17" cy="21" r="2" fill="#1f2937" />
          <path d="M29 21h0.01" stroke="#1f2937" strokeWidth="3" strokeLinecap="round" />
          <path d="M19 30c2 2 8 2 10 0" stroke="#0369A1" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      )
    case "avatar-6":
      return (
        <svg {...common}>
          <circle cx="24" cy="24" r="20" fill="#FECACA" stroke="#F87171" strokeWidth="1.5" />
          <rect x="14" y="18" width="8" height="6" rx="1.5" stroke="#7F1D1D" strokeWidth="1.3" fill="none" />
          <rect x="26" y="18" width="8" height="6" rx="1.5" stroke="#7F1D1D" strokeWidth="1.3" fill="none" />
          <circle cx="17" cy="21" r="1.2" fill="#7F1D1D" />
          <circle cx="31" cy="21" r="1.2" fill="#7F1D1D" />
          <path d="M20 30h8" stroke="#7F1D1D" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      )
    case "avatar-7":
      return (
        <svg {...common}>
          <path d="M14 16 L18 10 L22 16" fill="#E9D5FF" stroke="#A855F7" strokeWidth="1.2" />
          <path d="M26 16 L30 10 L34 16" fill="#E9D5FF" stroke="#A855F7" strokeWidth="1.2" />
          <circle cx="24" cy="26" r="18" fill="#F3E8FF" stroke="#C084FC" strokeWidth="1.5" />
          <circle cx="18" cy="24" r="2" fill="#581C87" />
          <circle cx="30" cy="24" r="2" fill="#581C87" />
          <path d="M20 31q4 3 8 0" stroke="#581C87" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      )
    case "avatar-8":
      return (
        <svg {...common}>
          <circle cx="24" cy="24" r="20" fill="#FFFBEB" stroke="#FCD34D" strokeWidth="1.5" />
          <circle cx="17" cy="22" r="2" fill="#1f2937" />
          <circle cx="31" cy="22" r="2" fill="#1f2937" />
          <ellipse cx="24" cy="31" rx="4" ry="2.5" fill="#F59E0B" opacity="0.35" />
        </svg>
      )
    case "avatar-9":
      return (
        <svg {...common}>
          <circle cx="24" cy="24" r="20" fill="#FCE7F3" stroke="#F472B6" strokeWidth="1.5" />
          <circle cx="17" cy="21" r="2" fill="#1f2937" />
          <circle cx="31" cy="21" r="2" fill="#1f2937" />
          <path d="M14 26l3 2 3-2M28 26l3 2 3-2" stroke="#EC4899" strokeWidth="1.2" strokeLinecap="round" fill="none" />
          <path d="M20 31h8" stroke="#9D174D" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      )
    case "avatar-10":
      return (
        <svg {...common}>
          <circle cx="24" cy="24" r="20" fill="#99F6E4" stroke="#2DD4BF" strokeWidth="1.5" />
          <path d="M16 23h4M28 23h4" stroke="#134E4A" strokeWidth="1.8" strokeLinecap="round" />
          <circle cx="18" cy="23" r="1" fill="#134E4A" />
          <circle cx="30" cy="23" r="1" fill="#134E4A" />
          <path d="M22 31h4" stroke="#0F766E" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      )
    default:
      return (
        <svg {...common}>
          <circle cx="24" cy="24" r="20" fill="#E5E7EB" />
        </svg>
      )
  }
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
            className="absolute inset-0 bg-black/55 backdrop-blur-sm"
            aria-label="关闭"
            onClick={onClose}
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby="lobby-avatar-picker-title"
            initial={{ opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.98 }}
            transition={{ type: "spring", stiffness: 380, damping: 28 }}
            className="relative z-[1] w-full max-w-[340px] overflow-hidden rounded-[1.5rem] border border-white/[0.12] bg-[#121214]/95 p-5 shadow-[0_24px_80px_rgba(0,0,0,0.65),inset_0_1px_0_rgba(255,255,255,0.06)]"
            style={{ WebkitBackdropFilter: "blur(28px)" }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id="lobby-avatar-picker-title" className="text-center text-[15px] font-semibold tracking-tight text-white">
              选一个头像
            </h2>
            <p className="mt-1 text-center text-[12px] text-white/45">简约卡通 · 仅保存在本机</p>
            <div className="mt-5 grid grid-cols-5 gap-2.5">
              {LOBBY_AVATAR_IDS.map((id) => {
                const active = id === currentId
                return (
                  <motion.button
                    key={id}
                    type="button"
                    onClick={() => onSelect(id)}
                    whileHover={{ scale: 1.06 }}
                    whileTap={{ scale: 0.94 }}
                    className={[
                      "flex aspect-square items-center justify-center rounded-2xl border p-1.5 transition-colors",
                      active
                        ? "border-white/50 bg-white/[0.15] shadow-[0_0_20px_rgba(255,255,255,0.12)]"
                        : "border-white/[0.08] bg-white/[0.04] hover:border-white/[0.2] hover:bg-white/[0.08]",
                    ].join(" ")}
                  >
                    <LobbyPresetAvatar id={id} className="h-full w-full" />
                  </motion.button>
                )
              })}
            </div>
            <button
              type="button"
              onClick={onClose}
              className="mt-5 w-full rounded-xl border border-white/[0.1] bg-white/[0.06] py-2.5 text-[13px] font-medium text-white/75 transition hover:bg-white/[0.1]"
            >
              完成
            </button>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}
