"use client"

import * as React from "react"
import { Music2, Volume2, VolumeX } from "lucide-react"
import { StagePortal } from "@/src/components/game-shell/StagePortal"

type Props = {
  src?: string
  basePath?: string
  storageKey: string
  className?: string
  /**
   * 页面底部存在 fixed 工具栏/CTADock（如大厅「开始匹配」）时置 true，
   * 将控制条上移避免与关键 CTA 点击区重叠。
   */
  elevated?: boolean
  /** 全屏弹层（规则/结算）打开时置 true：隐藏控制条，避免压在弹层按钮之上 */
  hidden?: boolean
}

const FILE_CANDIDATES = [
  "bgm.mp3",
  "bgm.wav",
  "music.mp3",
  "music.wav",
  "loop.mp3",
  "loop.wav",
  "theme.mp3",
  "theme.wav",
]

function normalizePublicAudioPath(path: string): string {
  const parts = path.split("/")
  return parts
    .map((seg, i) => {
      if (i === 0) return seg
      return encodeURIComponent(seg)
    })
    .join("/")
}

export function LoopingBgmControl({ src, basePath, storageKey, className = "", elevated = false, hidden = false }: Props) {
  const audioRef = React.useRef<HTMLAudioElement | null>(null)
  const lastNonZeroRef = React.useRef(0.6)
  const [open, setOpen] = React.useState(false)
  const [volume, setVolume] = React.useState(0.6)
  const [idx, setIdx] = React.useState(0)
  const [available, setAvailable] = React.useState(true)

  const resolvedSrc = React.useMemo(() => {
    if (src) return normalizePublicAudioPath(src)
    if (!basePath) return ""
    return normalizePublicAudioPath(`${basePath}/${FILE_CANDIDATES[idx]}`)
  }, [src, basePath, idx])

  React.useEffect(() => {
    try {
      const raw = localStorage.getItem(storageKey)
      if (raw == null) return
      const n = Number(raw)
      if (Number.isFinite(n)) setVolume(Math.max(0, Math.min(1, n)))
    } catch {
      /* ignore */
    }
  }, [storageKey])

  React.useEffect(() => {
    try {
      localStorage.setItem(storageKey, String(volume))
    } catch {
      /* ignore */
    }
  }, [storageKey, volume])

  React.useEffect(() => {
    const el = audioRef.current
    if (!el) return
    el.volume = volume
    el.muted = volume <= 0.001
  }, [volume])

  React.useEffect(() => {
    if (volume > 0.001) lastNonZeroRef.current = volume
  }, [volume])

  React.useEffect(() => {
    const el = audioRef.current
    if (!el) return

    const tryPlay = () => {
      void el.play().catch(() => {
        /* autoplay blocked until user interacts */
      })
    }

    tryPlay()
    window.addEventListener("pointerdown", tryPlay, { once: true })
    return () => window.removeEventListener("pointerdown", tryPlay)
  }, [resolvedSrc])

  const onAudioError = React.useCallback(() => {
    if (src) {
      setAvailable(false)
      return
    }
    if (idx < FILE_CANDIDATES.length - 1) {
      setIdx((v) => v + 1)
      return
    }
    setAvailable(false)
  }, [idx, src])

  if (!available || hidden) return null
  const audible = volume > 0.001

  const onPrimaryClick = () => {
    // First click: immediately mute and open slider panel for drag.
    if (!open) {
      setOpen(true)
      if (audible) setVolume(0)
      return
    }
    setOpen(false)
  }

  // portal 到 document.body：游戏页内 BGM 位于 ScaleFitGameStage 缩放容器中，
  // 不逃逸 transform 会随舞台缩到 <24px（rules §3）。
  return (
    <StagePortal>
      <audio ref={audioRef} src={resolvedSrc} loop preload="auto" onError={onAudioError} />

      <div
        className={`fixed right-[max(0.85rem,env(safe-area-inset-right))] z-[120] ${
          elevated
            ? "bottom-[max(5.5rem,calc(env(safe-area-inset-bottom)+4.5rem))]"
            : "bottom-[max(0.85rem,env(safe-area-inset-bottom))]"
        } ${className}`}
      >
        <div className="flex items-center gap-2 rounded-full border border-white/15 bg-black/55 px-2 py-1.5 shadow-[0_8px_28px_rgba(0,0,0,0.45)] backdrop-blur-md">
          <button
            type="button"
            onClick={onPrimaryClick}
            className="relative flex h-8 w-8 items-center justify-center rounded-full border border-white/16 bg-white/10 text-white/90 transition hover:bg-white/15"
            title="背景音乐"
            aria-label="背景音乐"
          >
            {audible ? (
              <>
                <span className="pointer-events-none absolute inset-0 rounded-full border border-white/40 opacity-80 animate-ping [animation-duration:1.8s]" />
                <span className="pointer-events-none absolute -inset-1 rounded-full border border-white/25 opacity-70 animate-ping [animation-duration:var(--duration-ambient)]" />
              </>
            ) : null}
            <span
              className={[
                "relative z-[1] flex h-6 w-6 items-center justify-center rounded-full border border-white/35 bg-gradient-to-br from-white/35 to-white/10",
                audible ? "animate-[spin_2.8s_linear_infinite]" : "",
              ].join(" ")}
            >
              <Music2 className="h-3.5 w-3.5" />
            </span>
          </button>

          {open ? (
            <div className="flex items-center gap-2 pr-1">
              <button
                type="button"
                className="flex h-8 w-8 items-center justify-center rounded-full text-white/80 transition hover:text-white"
                onClick={() => setVolume((v) => (v > 0.001 ? 0 : Math.max(0.2, lastNonZeroRef.current)))}
                title={volume > 0.001 ? "静音" : "恢复音量"}
                aria-label={volume > 0.001 ? "静音" : "恢复音量"}
              >
                {volume > 0.001 ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
              </button>
              <input
                type="range"
                min={0}
                max={100}
                step={1}
                value={Math.round(volume * 100)}
                onChange={(e) => setVolume(Number(e.target.value) / 100)}
                className="h-1.5 w-28 accent-white"
                aria-label="背景音乐音量"
              />
            </div>
          ) : null}
        </div>
      </div>
    </StagePortal>
  )
}

