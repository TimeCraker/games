"use client"

import * as React from "react"
import { AnimatePresence, motion } from "framer-motion"
import { StagePortal } from "@/src/components/game-shell/StagePortal"

/* ============================================================================
   LoopingBgmControl —— 2026-09-27 重做

   旧版问题（实测）：
   1. 白色玻璃 + 两个 animate-ping 光圈，读起来像「未读通知徽章」，不是音乐控件
   2. 用 lucide 的 Music2 + 原生 <input type=range>，完全没走琥珀设计系统
   3. 悬浮固定在右下，滚动时压住卡片内容（移动端已确认）
   4. 是纯装饰动画，与正在播放的音频毫无关系

   新版：
   - 外环 = 音量电平表（stroke-dashoffset 映射音量）
   - 内嵌 5 根微柱 = 真实频谱（Web Audio AnalyserNode）
   - 展开 = 10 段琥珀音量块（替代原生 range），role="slider" + 方向键可访问
   - 新增 variant="inline"：大厅放进顶栏，彻底消除悬浮遮挡

   Web Audio 的 4 个陷阱（均已处理，勿删）：
   a) createMediaElementSource 会切断元素默认输出 → 必须 connect(destination)
   b) 同一元素只能接管一次，重复调用抛 InvalidStateError → try/catch + 放弃可视化
   c) AudioContext 初始 suspended（自动播放策略）→ 用户手势里 resume()
   d) 原始频谱抖动剧烈 → 单极点滤波平滑，否则柱子像噪点
   ============================================================================ */

type Props = {
  src?: string
  basePath?: string
  storageKey: string
  className?: string
  /** 页面底部存在 fixed 工具栏/CTA Dock 时置 true，避免与关键 CTA 点击区重叠 */
  elevated?: boolean
  /** 全屏弹层打开时置 true：隐藏控件 */
  hidden?: boolean
  /** floating=游戏页悬浮（默认）｜inline=顶栏内联（大厅，避免遮挡内容） */
  variant?: "floating" | "inline"
  /**
   * 音频就绪（canplay，可开始播放）或确认不可用（error / 无源）或超时后，回调一次。
   * 用于「压住开始按钮直到音乐加载出来」。用 ref 保证只触发一次，重复调用幂等。
   */
  onReady?: () => void
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

const BARS = 5
const STEPS = 10
const RING_R = 19
const RING_C = 2 * Math.PI * RING_R

function normalizePublicAudioPath(path: string): string {
  const parts = path.split("/")
  return parts
    .map((seg, i) => (i === 0 ? seg : encodeURIComponent(seg)))
    .join("/")
}

export function LoopingBgmControl({
  src,
  basePath,
  storageKey,
  className = "",
  elevated = false,
  hidden = false,
  variant = "floating",
  onReady,
}: Props) {
  const audioRef = React.useRef<HTMLAudioElement | null>(null)
  const barRefs = React.useRef<Array<HTMLSpanElement | null>>([])
  const analyserRef = React.useRef<AnalyserNode | null>(null)
  const rafRef = React.useRef<number | null>(null)
  const smoothedRef = React.useRef<number[]>(new Array(BARS).fill(0))
  const lastNonZeroRef = React.useRef(0.6)
  // 就绪回调（压住「开始」按钮）：保证只触发一次
  const readyFiredRef = React.useRef(false)
  const onReadyRef = React.useRef<(() => void) | undefined>(undefined)

  const [open, setOpen] = React.useState(false)
  const [volume, setVolume] = React.useState(0.6)
  const [idx, setIdx] = React.useState(0)
  const [available, setAvailable] = React.useState(true)
  const [playing, setPlaying] = React.useState(false)
  const [reduceMotion, setReduceMotion] = React.useState(false)

  const resolvedSrc = React.useMemo(() => {
    if (src) return normalizePublicAudioPath(src)
    if (!basePath) return ""
    return normalizePublicAudioPath(`${basePath}/${FILE_CANDIDATES[idx]}`)
  }, [src, basePath, idx])

  /* ---------- 持久化音量 ---------- */
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

  /* ---------- 就绪回调（压住「开始」按钮直到音乐可播放） ---------- */
  React.useEffect(() => {
    onReadyRef.current = onReady
  }, [onReady])

  React.useEffect(() => {
    const el = audioRef.current
    const fire = () => {
      if (readyFiredRef.current) return
      readyFiredRef.current = true
      onReadyRef.current?.()
    }
    // 无音频源 / 元素尚未挂载：无需等待，直接放行
    if (!resolvedSrc || !el) {
      fire()
      return
    }
    // 已可播放（缓存命中 / 先一步加载完）：立即放行
    if (el.readyState >= 3) {
      fire()
      return
    }
    const onCan = () => {
      if (el.readyState >= 3) fire()
    }
    const onErr = () => fire() // 加载失败也别卡住游戏
    el.addEventListener("canplay", onCan)
    el.addEventListener("canplaythrough", onCan)
    el.addEventListener("error", onErr)
    // 网络卡死兜底：10s 后无论如何放行
    const timer = window.setTimeout(fire, 10000)
    return () => {
      el.removeEventListener("canplay", onCan)
      el.removeEventListener("canplaythrough", onCan)
      el.removeEventListener("error", onErr)
      window.clearTimeout(timer)
    }
  }, [resolvedSrc])

  React.useEffect(() => {
    if (typeof window === "undefined") return
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)")
    const on = () => setReduceMotion(mq.matches)
    on()
    mq.addEventListener?.("change", on)
    return () => mq.removeEventListener?.("change", on)
  }, [])

  /* ---------- Web Audio：接管 audio 元素做真实频谱 ---------- */
  React.useEffect(() => {
    const el = audioRef.current
    if (!el || typeof window === "undefined") return
    const AC: typeof AudioContext | undefined =
      window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    if (!AC) return

    let ctx: AudioContext
    try {
      ctx = new AC()
    } catch {
      return
    }
    const analyser = ctx.createAnalyser()
    analyser.fftSize = 128
    analyser.smoothingTimeConstant = 0.72

    let source: MediaElementAudioSourceNode
    try {
      source = ctx.createMediaElementSource(el)
    } catch {
      // (b) 该元素已被别的上下文接管 → 放弃可视化，但绝不能影响音频播放
      void ctx.close()
      return
    }
    // (a) 关键：不接 destination 就是静音
    try {
      source.connect(analyser)
      analyser.connect(ctx.destination)
    } catch {
      void ctx.close()
      return
    }
    analyserRef.current = analyser

    // (c) 自动播放策略：AudioContext 初始 suspended，需在用户手势里恢复
    const resume = () => {
      if (ctx.state === "suspended") void ctx.resume().catch(() => {})
    }
    resume()
    window.addEventListener("pointerdown", resume)
    window.addEventListener("keydown", resume)

    const freq = new Uint8Array(analyser.frequencyBinCount)

    const tick = () => {
      const a = analyserRef.current
      if (!a) return
      a.getByteFrequencyData(freq)
      const per = Math.floor(freq.length / BARS)
      for (let i = 0; i < BARS; i++) {
        let sum = 0
        for (let k = 0; k < per; k++) sum += freq[i * per + k] ?? 0
        const target = sum / per / 255
        // (d) 单极点滤波：起音快、回落慢，避免噪点感
        const prev = smoothedRef.current[i] ?? 0
        const k2 = target > prev ? 0.5 : 0.14
        const v = prev + (target - prev) * k2
        smoothedRef.current[i] = v
        const node = barRefs.current[i]
        if (node) node.style.transform = `scaleY(${(0.12 + v * 0.88).toFixed(3)})`
      }
      rafRef.current = window.requestAnimationFrame(tick)
    }

    const start = () => {
      if (rafRef.current == null && !reduceMotion) rafRef.current = window.requestAnimationFrame(tick)
    }
    const stop = () => {
      if (rafRef.current != null) {
        window.cancelAnimationFrame(rafRef.current)
        rafRef.current = null
      }
      // 停止时把柱子压平
      barRefs.current.forEach((n) => {
        if (n) n.style.transform = "scaleY(0.12)"
      })
      smoothedRef.current = smoothedRef.current.map(() => 0)
    }

    const onPlay = () => {
      setPlaying(true)
      start()
    }
    const onPause = () => {
      setPlaying(false)
      stop()
    }
    const onVis = () => {
      if (document.hidden) stop()
      else if (!el.paused) start()
    }

    el.addEventListener("play", onPlay)
    el.addEventListener("playing", onPlay)
    el.addEventListener("pause", onPause)
    el.addEventListener("ended", onPause)
    document.addEventListener("visibilitychange", onVis)
    if (!el.paused) onPlay()

    return () => {
      stop()
      el.removeEventListener("play", onPlay)
      el.removeEventListener("playing", onPlay)
      el.removeEventListener("pause", onPause)
      el.removeEventListener("ended", onPause)
      document.removeEventListener("visibilitychange", onVis)
      window.removeEventListener("pointerdown", resume)
      window.removeEventListener("keydown", resume)
      analyserRef.current = null
      try {
        source.disconnect()
        analyser.disconnect()
      } catch {
        /* ignore */
      }
      void ctx.close().catch(() => {})
    }
  }, [reduceMotion])

  /* ---------- 播放与错误回退 ---------- */
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
    return () => {
      window.removeEventListener("pointerdown", tryPlay)
      el.pause()
    }
  }, [resolvedSrc])

  React.useEffect(() => {
    return () => {
      const el = audioRef.current
      if (!el) return
      el.pause()
      el.removeAttribute("src")
      el.load()
    }
  }, [])

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

  const setVolumeSafe = React.useCallback((v: number) => {
    setVolume(Math.max(0, Math.min(1, v)))
  }, [])

  const onSliderKeyDown = (e: React.KeyboardEvent) => {
    const step = 0.1
    if (e.key === "ArrowRight" || e.key === "ArrowUp") {
      e.preventDefault()
      setVolumeSafe(volume + step)
    } else if (e.key === "ArrowLeft" || e.key === "ArrowDown") {
      e.preventDefault()
      setVolumeSafe(volume - step)
    } else if (e.key === "Home") {
      e.preventDefault()
      setVolumeSafe(0)
    } else if (e.key === "End") {
      e.preventDefault()
      setVolumeSafe(1)
    }
  }

  // 2026-09-27 修复：hidden 只收起「可见的表盘 / 音量面板」，不再一并卸载 <audio> 元素。
  // 否则教程 / 规则弹层打开期间 audio 不在 DOM、preload 无从发生，玩家点「开始」时
  // 音乐才开始下载 → 出现「游戏能玩了、音乐却还没加载出来」的别扭空窗（用户反馈）。
  if (!available) return null
  const audible = volume > 0.001

  // 2026-09-27：旧版「点一下同时展开并静音」在新版里反直觉
  // （面板中已有独立静音按钮），改为纯粹的展开/收起。
  const onPrimaryClick = () => setOpen((v) => !v)

  const dial = (
    <button
      type="button"
      onClick={onPrimaryClick}
      className="relative flex h-11 w-11 shrink-0 items-center justify-center focus-visible:outline-none"
      title="背景音乐"
      aria-label="背景音乐"
      aria-expanded={open}
    >
      {/* 外环 = 音量电平表 */}
      <svg viewBox="0 0 44 44" className="absolute inset-0 -rotate-90" aria-hidden>
        <circle cx="22" cy="22" r={RING_R} fill="none" strokeWidth="2" className="stroke-hud-line" />
        <circle
          cx="22"
          cy="22"
          r={RING_R}
          fill="none"
          strokeWidth="2"
          strokeLinecap="butt"
          strokeDasharray={RING_C}
          strokeDashoffset={RING_C * (1 - volume)}
          className="stroke-hud-accent transition-[stroke-dashoffset] duration-200 ease-out"
        />
      </svg>

      {/* 内嵌 5 根真实频谱柱 */}
      <span className="relative flex h-[14px] w-[18px] items-end justify-between" aria-hidden>
        {Array.from({ length: BARS }).map((_, i) => (
          <span
            key={i}
            ref={(el) => {
              barRefs.current[i] = el
            }}
            className="block h-full w-[2px] origin-bottom bg-hud-accent-bright"
            style={{ transform: "scaleY(0.12)" }}
          />
        ))}
      </span>

      {/* 静音：斜杠 */}
      {!audible ? (
        <span
          className="pointer-events-none absolute left-1/2 top-1/2 h-[2px] w-6 -translate-x-1/2 -translate-y-1/2 -rotate-45 bg-hud-red"
          aria-hidden
        />
      ) : null}

      {/* 播放中：极轻的外环呼吸（尊重 reduced-motion） */}
      {playing && !reduceMotion ? (
        <span className="pointer-events-none absolute inset-0 animate-pulse rounded-full ring-1 ring-hud-accent/25 [animation-duration:2.6s]" aria-hidden />
      ) : null}
    </button>
  )

  const floating = variant !== "inline"

  /** 音量面板：绝对定位的下拉/侧浮，展开不影响宿主布局宽度 */
  const volumePanel = (
    <motion.div
      initial={reduceMotion ? false : { opacity: 0, scale: 0.96, x: floating ? 6 : 0, y: floating ? 0 : -6 }}
      animate={{ opacity: 1, scale: 1, x: 0, y: 0 }}
      exit={reduceMotion ? undefined : { opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.18, ease: [0.32, 0.72, 0, 1] }}
      className={[
        "absolute z-20 flex items-center gap-2 border border-hud-line bg-ink-800/95 p-1.5 backdrop-blur-md",
        "shadow-[0_10px_32px_rgba(0,0,0,0.55)]",
        floating ? "bottom-0 right-full mr-2 origin-bottom-right" : "right-0 top-full mt-2 origin-top-right",
      ].join(" ")}
    >
      <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setVolumeSafe(audible ? 0 : Math.max(0.2, lastNonZeroRef.current))}
            className="flex h-8 w-8 shrink-0 items-center justify-center border border-hud-line text-hud-text-dim transition-colors duration-150 hover:border-hud-accent/50 hover:text-hud-accent focus-visible:outline-none"
            title={audible ? "静音" : "恢复音量"}
            aria-label={audible ? "静音" : "恢复音量"}
          >
            {audible ? <VolumeOnGlyph /> : <VolumeOffGlyph />}
          </button>

          {/* 10 段琥珀音量块；单一 slider 语义，避免 10 个 tab 落点 */}
          <div
            role="slider"
            tabIndex={0}
            aria-label="背景音乐音量"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(volume * 100)}
            onKeyDown={onSliderKeyDown}
            className="group/slider flex h-8 cursor-pointer items-center gap-[3px] px-0.5 focus-visible:outline-none"
          >
            {Array.from({ length: STEPS }).map((_, i) => {
              const on = volume * STEPS > i
              return (
                <span
                  key={i}
                  aria-hidden
                  onClick={() => setVolumeSafe((i + 1) / STEPS)}
                  className={[
                    "block h-[18px] w-[9px] border transition-colors duration-100",
                    on
                      ? "border-hud-accent/70 bg-hud-accent"
                      : "border-hud-line bg-ink-900/70 group-hover/slider:border-hud-accent/40",
                  ].join(" ")}
                />
              )
            })}
          </div>
        </div>
      </motion.div>
  )

  const shell = (
    <div className="relative">
      <div className="flex items-center border border-hud-line bg-ink-800/85 p-1 shadow-[0_8px_28px_rgba(0,0,0,0.5)] backdrop-blur-md transition-colors duration-200 hover:border-hud-accent/40">
        {dial}
      </div>
      <AnimatePresence>{open ? volumePanel : null}</AnimatePresence>
    </div>
  )

  // <audio> 无条件挂载：preload="auto" 在教程 / 简报期间就预热音源，见上方注释。
  const audioEl = <audio ref={audioRef} src={resolvedSrc} loop preload="auto" onError={onAudioError} />

  if (variant === "inline") {
    return (
      <div className={className}>
        {audioEl}
        {hidden ? null : shell}
      </div>
    )
  }

  return (
    <StagePortal>
      {audioEl}
      {hidden ? null : (
        <div
          className={`fixed right-[max(0.85rem,env(safe-area-inset-right))] z-[120] ${
            elevated
              ? "bottom-[max(5.5rem,calc(env(safe-area-inset-bottom)+4.5rem))]"
              : "bottom-[max(0.85rem,env(safe-area-inset-bottom))]"
          } ${className}`}
        >
          {shell}
        </div>
      )}
    </StagePortal>
  )
}

/* ---------- 内联小图标（替代 lucide，与 HUD 图标同规格：等宽描边 + 斜切端点） ---------- */

function VolumeOnGlyph() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="square" strokeLinejoin="miter" aria-hidden>
      <path d="M4 9.5h4L12.5 5.5v13L8 14.5H4z" />
      <path d="M16 9.5a3.5 3.5 0 0 1 0 5M19 7a7 7 0 0 1 0 10" />
    </svg>
  )
}

function VolumeOffGlyph() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="square" strokeLinejoin="miter" aria-hidden>
      <path d="M4 9.5h4L12.5 5.5v13L8 14.5H4z" />
      <path d="M16.5 9.5l5 5M21.5 9.5l-5 5" />
    </svg>
  )
}
