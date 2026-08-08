"use client"

import * as React from "react"

const CLICK_SFX_SRC = "/audio/sfx/ui/buttons/buttonclick.wav"

export function GlobalUiClickSfx() {
  const audioRef = React.useRef<HTMLAudioElement | null>(null)

  React.useEffect(() => {
    const playClick = (ev: PointerEvent) => {
      const target = ev.target as HTMLElement | null
      if (!target) return
      const interactive = target.closest("button, a, [role='button'], input[type='button'], input[type='submit']")
      if (!interactive) return

      const audio = audioRef.current
      if (!audio) return
      audio.currentTime = 0
      void audio.play().catch(() => {
        /* ignore autoplay errors */
      })
    }

    document.addEventListener("pointerdown", playClick, true)
    return () => document.removeEventListener("pointerdown", playClick, true)
  }, [])

  return <audio ref={audioRef} src={CLICK_SFX_SRC} preload="auto" />
}

