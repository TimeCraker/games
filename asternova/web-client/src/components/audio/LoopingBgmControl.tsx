"use client"

import * as React from "react"
import { Music2, Volume2, VolumeX } from "lucide-react"

type Props = {
  src?: string
  basePath?: string
  storageKey: string
  className?: string
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

export function LoopingBgmControl({ src, basePath, storageKey, className = "" }: Props) {
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

  if (!available) return null
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

  return (
    <>
      <audio ref={audioRef} src={resolvedSrc} loop preload="auto" onError={onAudioError} />

      <div
        className={`fixed bottom-[max(0.85rem,env(safe-area-inset-bottom))] right-[max(0.85rem,env(safe-area-inset-right))] z-[120] ${className}`}
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
                <span className="pointer-events-none absolute -inset-1 rounded-full border border-white/25 opacity-70 animate-ping [animation-duration:2.6s]" />
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
                className="text-white/80"
                onClick={() => setVolume((v) => (v > 0.001 ? 0 : Math.max(0.2, lastNonZeroRef.current)))}
                title={volume > 0.001 ? "静音" : "恢复音量"}
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
    </>
  )
}

