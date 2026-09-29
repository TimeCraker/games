"use client"

import * as React from "react"
import { AnimatePresence, motion, useReducedMotion } from "framer-motion"

import { cn } from "@/lib/utils"
import { easeInstrument, staggerDelay } from "@/src/lib/motion"

import { LEVELS } from "../engine/content/levels"
import { LockGlyph, StarGlyph } from "./BallGlyph"
import { useStaProgress } from "./useStaProgress"
import { totalStars } from "./staProgress"

/**
 * 选关 · Bento Grid + Spotlight Border（art bible §4.2）。
 *
 * 独立全屏页，真实 CSS px（不在 720×1280 缩放容器内，§4 开头标注）。
 * 四态：锁定 / 已解锁 / 通关 / 当前（featured，跨 2 列）。
 *
 * Spotlight Border 严格按 §4.2 规格：
 * 「光斑 = 卡片伪元素上的预烘焙径向渐变（半径 120px，--arcade-accent @35%→0），
 *   用 transform: translate(var(--mx), var(--my)) 随光标移动，禁 filter:blur 实时模糊」
 * → 渐变纹理本身烘焙固定，只有 transform 在动（合成器友好，不重算渐变）。
 *
 * 触屏（无 hover）退化为卡片中心 2.6s 呼吸柔光，transform-only（scale 呼吸），
 * 尊重 prefers-reduced-motion。
 *
 * R6 动效轮新增：
 * - 卡片群 stagger 入场（opacity+y14，500ms --ease-cinematic，每项 +30ms）；
 * - select↔game 真转场：根节点接入 StaRoot 的 AnimatePresence（exit fade+y 上行）；
 * - CURRENT 卡呼吸描边（.hud-breathe-ring，--duration-ambient 2.6s，opacity-only）；
 * - 锁定卡：可聚焦可点击（aria-disabled），点击 WAAPI shake ±3px + 底部提示浮层；
 * - 星星 check-pop（.hud-check-pop，随卡片入场逐星 +60ms 交错）。
 */

const MAX_LEVELS = LEVELS.length

/** 渐变半径 120px → 元素 240×240，中心即光斑心 */
const SPOT = 240

/** 锁定提示浮层自动消失时长 */
const LOCK_TIP_MS = 1600

/** WAAPI shake：±3px 水平抖动，160ms（rules.md §6 微交互 150–300ms 区间取下限） */
function shakeEl(el: HTMLElement | null): void {
  if (!el || typeof el.animate !== "function") return
  el.animate(
    [
      { transform: "translateX(0)" },
      { transform: "translateX(-3px)" },
      { transform: "translateX(3px)" },
      { transform: "translateX(-3px)" },
      { transform: "translateX(3px)" },
      { transform: "translateX(0)" },
    ],
    { duration: 160, easing: "cubic-bezier(0.32, 0.72, 0, 1)" },
  )
}

export function StaLevelSelect({ onPick }: { onPick: (levelId: number) => void }) {
  const progress = useStaProgress()
  const stars = totalStars(progress, MAX_LEVELS)
  const reduceMotion = useReducedMotion()

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

  // 锁定提示浮层（单实例，重复点击重置计时）
  const [lockTip, setLockTip] = React.useState<{ key: number; levelId: number } | null>(null)
  const lockTipTimer = React.useRef<number | null>(null)
  const tipKey = React.useRef(0)
  React.useEffect(() => {
    return () => {
      if (lockTipTimer.current !== null) window.clearTimeout(lockTipTimer.current)
    }
  }, [])
  const onLockedClick = React.useCallback((levelId: number) => {
    tipKey.current += 1
    setLockTip({ key: tipKey.current, levelId })
    if (lockTipTimer.current !== null) window.clearTimeout(lockTipTimer.current)
    lockTipTimer.current = window.setTimeout(() => setLockTip(null), LOCK_TIP_MS)
  }, [])

  // 转场期间防误触：exit 动画进行中卡片仍挂载，拦截二次 pick
  const pickedRef = React.useRef(false)
  const handlePick = React.useCallback(
    (levelId: number) => {
      if (pickedRef.current) return
      pickedRef.current = true
      onPick(levelId)
    },
    [onPick],
  )

  return (
    <motion.div
      initial={reduceMotion ? false : { opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={reduceMotion ? undefined : { opacity: 0, y: -12 }}
      transition={{ duration: 0.3, ease: easeInstrument }}
      className="absolute inset-0 z-40 overflow-y-auto overscroll-contain"
    >
      <div className="star-chart-grid min-h-full bg-ink-1000">
        <div className="mx-auto w-full max-w-[420px] px-4 pb-16 pt-[max(1.25rem,env(safe-area-inset-top))]">
          <motion.header
            initial={reduceMotion ? false : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: easeInstrument }}
            className="mb-5 flex items-end justify-between gap-3"
          >
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
          </motion.header>

          <SpotlightCard
            levelId={currentId}
            state="current"
            onPick={handlePick}
            onLockedClick={onLockedClick}
            enterIndex={0}
            featured
          />

          <div className="mt-3 grid grid-cols-2 gap-3">
            {rest.map((l, i) => {
              const rec = progress.levels[String(l.id)]
              const unlocked = l.id === 1 || rec?.unlocked === true
              const cleared = rec?.cleared === true
              const state: CardState = !unlocked ? "locked" : cleared ? "cleared" : "unlocked"
              return (
                <SpotlightCard
                  key={l.id}
                  levelId={l.id}
                  state={state}
                  onPick={handlePick}
                  onLockedClick={onLockedClick}
                  enterIndex={i + 1}
                />
              )
            })}
          </div>
        </div>
      </div>

      {/* 锁定提示浮层：fade+slide 进出（200ms），不挡操作 */}
      <AnimatePresence>
        {lockTip ? (
          <motion.div
            key={lockTip.key}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2, ease: easeInstrument }}
            className="pointer-events-none fixed inset-x-0 bottom-[max(1.5rem,env(safe-area-inset-bottom))] z-50 flex justify-center px-4"
          >
            <span className="hud-chamfer-sm flex items-center gap-2 border border-hud-line bg-ink-800/95 px-4 py-2.5 text-[13px] text-hud-text-dim">
              <LockGlyph size={13} className="text-hud-text-faint" />
              先通过第 {lockTip.levelId - 1} 关
            </span>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </motion.div>
  )
}

type CardState = "locked" | "unlocked" | "cleared" | "current"

function SpotlightCard({
  levelId,
  state,
  onPick,
  onLockedClick,
  enterIndex,
  featured = false,
}: {
  levelId: number
  state: CardState
  onPick: (id: number) => void
  /** 锁定卡点击回调（shake 由卡片自理，提示浮层由父级统一挂） */
  onLockedClick: (id: number) => void
  /** stagger 入场次序（featured = 0，其余按网格序 +1） */
  enterIndex: number
  featured?: boolean
}) {
  const def = LEVELS.find((l) => l.id === levelId)
  const progress = useStaProgress()
  const rec = progress.levels[String(levelId)]
  const stars = rec?.stars ?? 0
  const best = rec?.bestScore ?? 0
  const ref = React.useRef<HTMLButtonElement | null>(null)
  const reduceMotion = useReducedMotion()

  const [hovered, setHovered] = React.useState(false)
  const [origin, setOrigin] = React.useState<{ x: number; y: number } | null>(null)
  const [touchOnly, setTouchOnly] = React.useState(false)

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
      : "cursor-pointer transition-[translate,scale,border-color] duration-150 ease-[var(--ease-instrument)] hover:-translate-y-[2px] hover:border-hud-accent/60 active:scale-[0.98]",
    featured ? "p-4" : "p-3",
    state === "locked" && "border border-hud-line bg-ink-900",
    state === "unlocked" && "border border-hud-line bg-ink-800",
    state === "cleared" && "border border-[color:var(--hud-accent)]/40 bg-ink-800",
    state === "current" && "border-[1.5px] border-hud-accent bg-ink-700",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hud-accent/60",
  )

  const enterDelay = staggerDelay(enterIndex, 0.03)

  return (
    <motion.button
      ref={ref}
      type="button"
      // 锁定卡保持可点击以给出 shake+提示反馈（R6）；语义态用 aria-disabled 表达
      aria-disabled={locked || undefined}
      aria-label={
        locked
          ? `第 ${levelId} 关 ${def.name}，未解锁`
          : `第 ${levelId} 关 ${def.name}，目标 ${def.targetScore}，${stars} 星`
      }
      className={shell}
      initial={reduceMotion ? false : { opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1], delay: enterDelay }}
      onPointerMove={onMove}
      onPointerEnter={() => setHovered(true)}
      onPointerLeave={() => {
        setHovered(false)
      }}
      onFocus={() => setHovered(true)}
      onBlur={() => setHovered(false)}
      onClick={() => {
        if (locked) {
          if (!reduceMotion) shakeEl(ref.current)
          onLockedClick(levelId)
          return
        }
        onPick(levelId)
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

      {/* 当前关：呼吸描边（覆盖按钮自身边框像素，opacity 0.45↔1，2.6s ambient） */}
      {state === "current" ? (
        <span
          aria-hidden
          className="hud-breathe-ring pointer-events-none absolute border-[1.5px] border-hud-accent"
          style={{ top: -1.5, right: -1.5, bottom: -1.5, left: -1.5 }}
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
          {[0, 1, 2].map((i) => {
            const filled = !locked && i < stars
            // 星星随卡片入场逐星 pop（+60ms 交错）；空心星静态
            return (
              <span
                key={i}
                className={cn("inline-flex", filled && "hud-check-pop")}
                style={filled ? { animationDelay: `${enterDelay + 0.35 + i * 0.06}s` } : undefined}
              >
                <StarGlyph
                  filled={filled}
                  size={featured ? 15 : 13}
                  color={state === "cleared" ? "var(--hud-accent-bright)" : "var(--hud-accent)"}
                  hollowColor={locked ? "var(--ink-500)" : "var(--hud-line-strong)"}
                />
              </span>
            )
          })}
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
    </motion.button>
  )
}
