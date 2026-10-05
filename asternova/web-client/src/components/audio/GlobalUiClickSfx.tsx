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

  // 性能优化 2026-10：preload="none"——此 WAV（144KB）挂在根布局、每页都载，
  // 预载字节会挤占 Slow 4G 下的关键带宽；首次点击时 play() 自动触发加载，
  // 仅极首次点击有可感知延迟，之后走浏览器缓存瞬时播放。
  return <audio ref={audioRef} src={CLICK_SFX_SRC} preload="none" />
}

