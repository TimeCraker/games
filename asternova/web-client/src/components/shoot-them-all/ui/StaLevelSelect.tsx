"use client"

import * as React from "react"
import { motion, useReducedMotion } from "framer-motion"

import { cn } from "@/lib/utils"

import { LEVELS } from "../engine/content/levels"
import { LockGlyph, StarGlyph } from "./BallGlyph"
import { useStaProgress } from "./useStaProgress"
import { totalStars } from "./staProgress"

/**
 * 选关 · Bento Grid + Spotlight Border（art bible §4.2）。
 *
 * 独立全屏页，真实 CSS px（不在 720×1280 缩放容��内，§4 开头标注）。
 * 四态：锁定 / 已解锁 / 通关 / 当前（featured，跨 2 列）。
 *
 * Spotlight Border 严格按 §4.2 规格：
 * 「光斑 = 卡片伪元素上的预烘焙径向渐变（半径 120px，--arcade-accent @35%→0），
 *   用 transform: translate(var(--mx), var(--my)) 随光标移动，禁 filter:blur 实时模糊」
 * → 渐变纹理本身烘焙固定，只有 transform 在动（合成器友好，不重算渐变）。
 *
 * 触屏（无 hover）退化为卡片中心 2.6s 呼吸柔光，transform-only（scale 呼吸），
 * 尊重 prefers-reduced-motion。
 */

const MAX_LEVELS = LEVELS.length

/** 渐变半径 120px → 元素 240×240，中心即光斑心 */
const SPOT = 240

export function StaLevelSelect({ onPick }: { onPick: (levelId: number) => void }) {
  const progress = useStaProgress()
  const stars = totalStars(progress, MAX_LEVELS)

  // 当前关 = 首个已解锁但未通关的关；全通则落在最后一关
  const currentId = React.useMemo(() => {
    for (const l of LEVELS) {
      const rec = progress.levels[String(l.id)]
      const unlocked = l.id === 1 || rec?.unlocked === true
      if (unlocked && rec?.cleared !== true) return l.id
    }
    return LEVELS[LEVELS.length - 1].id
  }, [progress])

  const rest = LEVELS.filter((l) => l.id !== currentId)

  return (
    <div className="absolute inset-0 z-40 overflow-y-auto overscroll-contain">
      <div className="star-chart-grid min-h-full bg-ink-1000">
        <div className="mx-auto w-full max-w-[420px] px-4 pb-16 pt-[max(1.25rem,env(safe-area-inset-top))]">
          <header className="mb-5 flex items-end justify-between gap-3">
            <div>
              <h1 className="font-display text-[22px] leading-none tracking-[0.08em] text-hud-text">
                LEVEL SELECT
              </h1>
              <p className="mt-1.5 text-[12px] tracking-[0.14em] text-hud-text-faint">选择关卡</p>
            </div>
            <div className="flex items-center gap-1.5 border border-hud-line bg-ink-800/80 px-3 py-1.5">
              <StarGlyph filled size={13} color="var(--hud-accent)" />
              <span className="font-mono-data text-[13px] tabular-nums text-hud-text">
                {stars}/{MAX_LEVELS * 3}
              </span>
            </div>
          </header>

          <SpotlightCard
            levelId={currentId}
            state="current"
            onPick={onPick}
            featured
          />

          <div className="mt-3 grid grid-cols-2 gap-3">
            {rest.map((l) => {
              const rec = progress.levels[String(l.id)]
              const unlocked = l.id === 1 || rec?.unlocked === true
              const cleared = rec?.cleared === true
              const state: CardState = !unlocked ? "locked" : cleared ? "cleared" : "unlocked"
              return <SpotlightCard key={l.id} levelId={l.id} state={state} onPick={onPick} />
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

type CardState = "locked" | "unlocked" | "cleared" | "current"

function SpotlightCard({
  levelId,
  state,
  onPick,
  featured = false,
}: {
  levelId: number
  state: CardState
  onPick: (id: number) => void
  featured?: boolean
}) {
  const def = LEVELS.find((l) => l.id === levelId)
  const progress = useStaProgress()
  const rec = progress.levels[String(levelId)]
  const stars = rec?.stars ?? 0
  const best = rec?.bestScore ?? 0
  const ref = React.useRef<HTMLButtonElement | null>(null)

  const [hovered, setHovered] = React.useState(false)
  const [origin, setOrigin] = React.useState<{ x: number; y: number } | null>(null)
  const [touchOnly, setTouchOnly] = React.useState(false)
  const reduceMotion = useReducedMotion()

  React.useEffect(() => {
    if (typeof window === "undefined") return
    const mq = window.matchMedia("(hover: none)")
    const on = () => setTouchOnly(mq.matches)
    on()
    mq.addEventListener?.("change", on)
    return () => mq.removeEventListener?.("change", on)
  }, [])

  const onMove = React.useCallback((e: React.PointerEvent<HTMLButtonElement>) => {
    const el = ref.current
    if (!el) return
    const r = el.getBoundingClientRect()
    // 光斑是 240×240 的预烘焙块，要把它的「中心」送到指针处
    setOrigin({ x: e.clientX - r.left - SPOT / 2, y: e.clientY - r.top - SPOT / 2 })
  }, [])

  if (!def) return null

  const locked = state === "locked"
  const showSpot = !locked && !touchOnly && (hovered || origin !== null)

  const shell = cn(
    "group relative w-full overflow-hidden text-left",
    locked
      ? "cursor-not-allowed"
      : "cursor-pointer transition-transform duration-150 hover:-translate-y-[2px] active:scale-[0.98]",
    featured ? "p-4" : "p-3",
    state === "locked" && "border border-hud-line bg-ink-900",
    state === "unlocked" && "border border-hud-line bg-ink-800",
    state === "cleared" && "border border-[color:var(--hud-accent)]/40 bg-ink-800",
    state === "current" && "border-[1.5px] border-hud-accent bg-ink-700",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hud-accent/60",
  )

  return (
    <button
      ref={ref}
      type="button"
      disabled={locked}
      aria-label={
        locked
          ? `第 ${levelId} 关 ${def.name}，未解锁`
          : `第 ${levelId} 关 ${def.name}，目标 ${def.targetScore}，${stars} 星`
      }
      className={shell}
      onPointerMove={onMove}
      onPointerEnter={() => setHovered(true)}
      onPointerLeave={() => {
        setHovered(false)
      }}
      onFocus={() => setHovered(true)}
      onBlur={() => setHovered(false)}
      onClick={() => {
        if (!locked) onPick(levelId)
      }}
    >
      {/* Spotlight Border：预烘焙径向渐变块，只有 transform 在动（禁 blur / 禁改渐变中心） */}
      {!locked && !touchOnly ? (
        <span
          aria-hidden
          className={cn(
            "pointer-events-none absolute left-0 top-0 transition-opacity duration-200",
            showSpot ? "opacity-100" : "opacity-0",
          )}
          style={{
            width: SPOT,
            height: SPOT,
            transform: origin
              ? `translate(${origin.x}px, ${origin.y}px)`
              : "translate(0, 0)",
            background:
              "radial-gradient(circle closest-side, color-mix(in oklab, var(--arcade-accent) 35%, transparent), transparent 100%)",
            transitionTimingFunction: "var(--ease-instrument)",
          }}
        />
      ) : null}

      {/* 触屏退化：卡片中心 2.6s 呼吸柔光，transform-only（scale） */}
      {!locked && touchOnly ? (
        <motion.span
          aria-hidden
          className="pointer-events-none absolute left-1/2 top-1/2 h-44 w-44"
          style={{
            marginLeft: -88,
            marginTop: -88,
            background:
              "radial-gradient(circle closest-side, color-mix(in oklab, var(--arcade-accent) 24%, transparent), transparent 100%)",
          }}
          animate={
            reduceMotion
              ? { scale: 1, opacity: 0.5 }
              : { scale: [1, 1.18, 1], opacity: [0.45, 0.85, 0.45] }
          }
          transition={
            reduceMotion
              ? { duration: 0 }
              : { duration: 2.6, repeat: Infinity, ease: "easeInOut" }
          }
        />
      ) : null}

      {/* 通关：左上角 6px 琥珀刻角常亮 */}
      {state === "cleared" ? (
        <span
          aria-hidden
          className="pointer-events-none absolute left-0 top-0 h-3 w-3 border-l-2 border-t-2 border-hud-accent"
        />
      ) : null}

      {/* 当前关：顶部 2px 琥珀进度条（历史最佳 / 目标） */}
      {state === "current" ? (
        <span aria-hidden className="absolute inset-x-0 top-0 h-[2px] bg-hud-sunken">
          <span
            className="block h-full bg-hud-accent"
            style={{
              width: `${Math.min(100, Math.round((best / Math.max(1, def.targetScore)) * 100))}%`,
            }}
          />
        </span>
      ) : null}

      <div className="relative z-10">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-baseline gap-2.5">
            <span
              className={cn(
                "font-display leading-none",
                featured ? "text-[32px]" : "text-[26px]",
                locked ? "text-hud-line-strong" : "text-hud-accent",
              )}
              style={{ letterSpacing: "0.04em" }}
            >
              {String(def.id).padStart(2, "0")}
            </span>
            <span
              className={cn(
                "text-[15px] tracking-[0.02em]",
                locked ? "text-hud-text-faint" : "text-hud-text",
              )}
            >
              {def.name}
            </span>
          </div>
          {locked ? <LockGlyph size={14} className="mt-0.5 text-hud-line-strong" /> : null}
        </div>

        <div className="mt-2 flex items-center gap-1">
          {[0, 1, 2].map((i) => (
            <StarGlyph
              key={i}
              filled={!locked && i < stars}
              size={featured ? 15 : 13}
              color={state === "cleared" ? "var(--hud-accent-bright)" : "var(--hud-accent)"}
              hollowColor={locked ? "var(--ink-500)" : "var(--hud-line-strong)"}
            />
          ))}
          {state === "current" ? (
            <span className="ml-2 font-mono-data text-[11px] tracking-[0.22em] text-hud-accent">
              CURRENT
            </span>
          ) : null}
        </div>

        <div
          className={cn(
            "mt-2 font-mono-data text-[12px] tracking-[0.06em]",
            locked ? "text-hud-text-faint" : "text-hud-text-dim",
          )}
        >
          {locked ? (
            "未解锁"
          ) : (
            <>
              目标 {def.targetScore.toLocaleString("en-US")} · {def.balls.length} 球
              {best > 0 ? (
                <span className="ml-2 text-hud-text-faint">
                  最佳 {best.toLocaleString("en-US")}
                </span>
              ) : null}
            </>
          )}
        </div>
      </div>
    </button>
  )
}
