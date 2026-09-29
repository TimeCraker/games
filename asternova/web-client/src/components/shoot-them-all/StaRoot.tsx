"use client"

import * as React from "react"
import { AnimatePresence, MotionConfig, useReducedMotion } from "framer-motion"

import { LoopingBgmControl } from "@/src/components/audio/LoopingBgmControl"
import { BrandMark } from "@/src/components/arcade/BrandMark"
import { useArcadeAccent } from "@/src/components/arcade/useArcadeAccent"
import { GameBackButton } from "@/src/components/ui/GameBackButton"

import type { BallKind } from "./engine/types"
import type { GameEngine } from "./engine/GameEngine"
import { HEIGHT, WIDTH } from "./constants"
import { LEVELS } from "./engine/content/levels"
import { LEVEL_1_HINTS, StaHud } from "./StaHud"
import { StaGameShell } from "./StaGameShell"
import { StaPixiApp } from "./render/StaPixiApp"
import { StaLevelSelect } from "./ui/StaLevelSelect"
import { StaPausePanel } from "./ui/StaPausePanel"
import { StaResult, type StaResultData } from "./ui/StaResult"
import { recordLevelResult } from "./ui/staProgress"
import { useStaProgress } from "./ui/useStaProgress"

/**
 * Shoot Them All 顶层根 —— 游戏流程编排 + 输入→引擎桥接 + 浮层编排。
 *
 * 流程状态机（UI 层自己的 screen，独立于引擎 StaPhase）：
 *
 *   select ──pick(levelId)──▶ game ──level-clear/fail──▶ result ──┬─next/retry─▶ game
 *      ▲                          │  ▲                           └─exit──────▶ select
 *      └──────────exit────────────┘  └──────────pause/resume────────┘
 *
 * 相位同步：引擎 onEvent 是单一回调槽，已由渲染层（BattleScene）占用，
 * 故 UI 不去抢 —— 用 hudSnapshot() 轮询相位（level-clear / level-fail 是粘性终态，
 * 引擎会一直停在该相位等 UI 调 startLevel/restartLevel，100ms 轮询必能捕获）。
 *
 * 指针分层（§7）：瞄准/发射只发生在画布层；球托与暂停钮是 HUD 层的独立命中区，
 * 事件不冒泡到画布 → Dock 拖动只切球不发射。画布手势用 pointer capture 保证
 * 拖拽连贯（拖到 Dock 上空也不丢 move/up）。
 */

type Screen = "select" | "game"
type Overlay = null | "pause" | "result"

const MAX_LEVEL = LEVELS.length
const CLEAR_BANNER_MS = 380
const FAIL_BEAT_MS = 300

export function StaRoot() {
  useArcadeAccent("shoot-them-all")
  const reduceMotion = useReducedMotion()

  const hostRef = React.useRef<HTMLDivElement | null>(null)
  const pixiRef = React.useRef<StaPixiApp | null>(null)
  // 注：StaPixiApp.gameEngine 是 getter，类型已是返回值本身，套 ReturnType<> 会报错。
  const engineRef = React.useRef<GameEngine | null>(null)
  const [engine, setEngine] = React.useState<GameEngine | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  // ---- 流程状态 ----
  const [screen, setScreen] = React.useState<Screen>("select")
  const [overlay, setOverlay] = React.useState<Overlay>(null)
  const [result, setResult] = React.useState<StaResultData | null>(null)
  const [clearBanner, setClearBanner] = React.useState(false)
  const [totalBalls, setTotalBalls] = React.useState(0)
  // 初值 null 而非 0：0 会被教学条当成「已推进」信号，挂载即误跳首条提示
  const [hintSignal, setHintSignal] = React.useState<number | null>(null)
  const [hintDismissed, setHintDismissed] = React.useState(false)

  const progress = useStaProgress()
  const level1Done = React.useMemo(
    () => progress.hintsSeen.filter((id) => id.startsWith("1:")).length >= LEVEL_1_HINTS.length,
    [progress.hintsSeen],
  )

  /* ------------------------------------------------------------------ */
  /* Pixi 主机生命周期                                                   */
  /* ------------------------------------------------------------------ */
  React.useEffect(() => {
    const host = hostRef.current
    if (!host) return

    // Pixi v8 会在初始化期间注入 1×1 无语义 accessibility 按钮节点，是键盘 Tab 的隐形陷阱。
    const cleanPixiA11yNodes = () => {
      host
        .querySelectorAll<HTMLElement>('button[title*="enable accessibility"], [aria-label*="enable accessibility"]')
        .forEach((n) => n.remove())
    }
    cleanPixiA11yNodes()
    const mo = new MutationObserver(cleanPixiA11yNodes)
    mo.observe(host, { childList: true, subtree: true })

    const pixi = new StaPixiApp()
    pixiRef.current = pixi
    let cancelled = false

    pixi
      .mount(host)
      .then(() => {
        if (cancelled) {
          pixi.destroy()
          return
        }
        engineRef.current = pixi.gameEngine
        setEngine(pixi.gameEngine)
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      })

    return () => {
      mo.disconnect()
      cancelled = true
      pixi.destroy()
      pixiRef.current = null
      engineRef.current = null
      setEngine(null)
    }
  }, [])

  /* ------------------------------------------------------------------ */
  /* 相位同步：轮询 hudSnapshot，捕获 level-clear / level-fail 终态       */
  /* ------------------------------------------------------------------ */
  const settledRef = React.useRef(false)

  React.useEffect(() => {
    if (!engine) return
    settledRef.current = false
    const id = window.setInterval(() => {
      const snap = engine.hudSnapshot()
      if (settledRef.current) return

      if (snap.phase === "level-clear") {
        settledRef.current = true
        const stars = Math.max(1, Math.min(3, snap.stars))
        // 立刻落进度（星级 / 解锁 / 最佳分），再播 CLEAR 横幅，最后上结算
        recordLevelResult({ id: snap.levelId, stars, score: snap.score, cleared: true })
        setClearBanner(true)
        window.setTimeout(() => {
          setClearBanner(false)
          setResult({
            levelId: snap.levelId,
            score: snap.score,
            targetScore: snap.targetScore,
            stars,
            ballsLeft: snap.ballsLeft,
            bestCombo: snap.bestCombo,
          })
          setOverlay("result")
        }, reduceMotion ? 0 : CLEAR_BANNER_MS)
      } else if (snap.phase === "level-fail") {
        settledRef.current = true
        recordLevelResult({ id: snap.levelId, stars: 0, score: snap.score, cleared: false })
        window.setTimeout(() => {
          setResult({
            levelId: snap.levelId,
            score: snap.score,
            targetScore: snap.targetScore,
            stars: 0,
            ballsLeft: snap.ballsLeft,
            bestCombo: snap.bestCombo,
          })
          setOverlay("result")
        }, reduceMotion ? 0 : FAIL_BEAT_MS)
      }
    }, 100)
    return () => window.clearInterval(id)
  }, [engine, reduceMotion])

  /* ------------------------------------------------------------------ */
  /* 指针输入 → 引擎桥接                                                  */
  /* ------------------------------------------------------------------ */
  const activePointer = React.useRef<number | null>(null)

  const toLogical = React.useCallback((clientX: number, clientY: number) => {
    const host = hostRef.current
    if (!host) return null
    const rect = host.getBoundingClientRect()
    if (rect.width === 0 || rect.height === 0) return null
    return {
      x: ((clientX - rect.left) / rect.width) * WIDTH,
      y: ((clientY - rect.top) / rect.height) * HEIGHT,
    }
  }, [])

  const inputLive = screen === "game" && overlay === null && !clearBanner

  const onPointerMove = React.useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (!inputLive) return
      const p = toLogical(e.clientX, e.clientY)
      if (p) engineRef.current?.setAimFromPoint(p.x, p.y)
    },
    [inputLive, toLogical],
  )

  const onPointerDown = React.useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (!inputLive) return
      // capture 保证拖拽期间 move/up 都回到画布层（哪怕指针掠过球托/暂停钮）
      try {
        e.currentTarget.setPointerCapture(e.pointerId)
      } catch {
        /* 某些 WebView 不支持，退化为普通事件 */
      }
      activePointer.current = e.pointerId
      const p = toLogical(e.clientX, e.clientY)
      if (p) engineRef.current?.setAimFromPoint(p.x, p.y)
    },
    [inputLive, toLogical],
  )

  const onPointerUp = React.useCallback(() => {
    if (activePointer.current === null) return
    activePointer.current = null
    if (!inputLive) return
    const engine = engineRef.current
    if (!engine) return
    engine.launch()
    // 发出第一球 → 推进教学提示条
    setHintSignal((v) => (v ?? 0) + 1)
  }, [inputLive])

  /* ------------------------------------------------------------------ */
  /* 流程动作                                                            */
  /* ------------------------------------------------------------------ */
  const startLevel = React.useCallback((levelId: number) => {
    const engine = engineRef.current
    if (!engine) return
    engine.startLevel(levelId)
    // 球组总数在开局那一刻定格（之后队列只减不增），供 HUD 渲染已打出的空心位
    setTotalBalls(engine.hudSnapshot().ballQueue.length)
    settledRef.current = false
    setResult(null)
    setOverlay(null)
    setClearBanner(false)
    setHintDismissed(false)
    setScreen("game")
  }, [])

  const goSelect = React.useCallback(() => {
    setOverlay(null)
    setResult(null)
    setClearBanner(false)
    setScreen("select")
  }, [])

  const retry = React.useCallback(() => {
    const engine = engineRef.current
    if (!engine) return
    engine.restartLevel()
    setTotalBalls(engine.hudSnapshot().ballQueue.length)
    settledRef.current = false
    setResult(null)
    setOverlay(null)
    setClearBanner(false)
    setScreen("game")
  }, [])

  const next = React.useCallback(
    (levelId: number) => {
      if (levelId >= MAX_LEVEL) {
        // 末关通关：不再 wrap 回第 1 关，交回选关让玩家挑重打
        goSelect()
        return
      }
      startLevel(levelId + 1)
    },
    [goSelect, startLevel],
  )

  const openPause = React.useCallback(() => {
    setOverlay((v) => (v === null ? "pause" : v))
  }, [])
  const closePause = React.useCallback(() => setOverlay((v) => (v === "pause" ? null : v)), [])

  // Esc：对局中开/关暂停
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return
      if (screen !== "game" || clearBanner) return
      e.preventDefault()
      setOverlay((v) => (v === "pause" ? null : v === null ? "pause" : v))
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [screen, clearBanner])

  const hints = screen === "game" && !level1Done && !hintDismissed ? LEVEL_1_HINTS : []
  const lastLevel = result ? result.levelId >= MAX_LEVEL : false

  return (
    <MotionConfig reducedMotion="user">
      {/* 游戏本体：等比缩放容器（画布 + HUD 层，逻辑 px） */}
      <StaGameShell>
        <div
          ref={hostRef}
          className="absolute inset-0 z-0"
          style={{ touchAction: "none" }}
          onPointerMove={onPointerMove}
          onPointerDown={onPointerDown}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
        />

        {/* 对局 HUD 只在对局态渲染：选关屏下不留隐形 Tab 落点（暂停钮 / 球托槽） */}
        {screen === "game" ? (
          <StaHud
            engine={engine}
            totalBalls={totalBalls}
            clearBanner={clearBanner}
            onPause={openPause}
            onBallSelect={(kind: BallKind) => engineRef.current?.selectBall(kind)}
            hints={hints}
            hintAdvanceSignal={hintSignal}
            onHintDismiss={() => setHintDismissed(true)}
            seenHintIds={progress.hintsSeen}
            interactive={inputLive}
          />
        ) : null}

        {/* 品牌字随画布缩放（装饰）；返回钮保持真实命中区，移出缩放容器 */}
        <div className="pointer-events-none absolute inset-x-0 top-0 z-20 flex items-center justify-end p-3">
          <BrandMark slug="shoot-them-all" />
        </div>

        {error ? (
          <div className="absolute inset-0 z-30 flex items-center justify-center bg-black/70 p-6 text-center text-sm text-white/80">
            引擎初始化失败：{error}
          </div>
        ) : null}
      </StaGameShell>

      {/* 真实 CSS px 浮层：选关 / 暂停 / 结算（§4 开头：浮层在缩放容器外） */}
      <AnimatePresence>
        {screen === "select" ? (
          <StaLevelSelect key="select" onPick={startLevel} />
        ) : null}
      </AnimatePresence>

      <StaPausePanel
        open={screen === "game" && overlay === "pause"}
        levelId={engine?.hudSnapshot().levelId ?? 1}
        levelName={engine?.hudSnapshot().levelName ?? ""}
        score={engine?.hudSnapshot().score ?? 0}
        targetScore={engine?.hudSnapshot().targetScore ?? 0}
        ballsLeft={engine?.hudSnapshot().ballsLeft ?? 0}
        onResume={closePause}
        onRestart={retry}
        onExit={goSelect}
      >
        {/*
          音量行（art bible §4.4 条目 5）内嵌 BGM 控件。
          单实例 + 面板常驻挂载：audio 元素不随暂停卸载，BGM 跨暂停连续播放。
          用 inline 变体（不走 StagePortal 的 fixed 定位），落进面板布局。
          旧版的底部悬浮盘已撤掉 —— 两处各挂一个会出双音频。
        */}
        <LoopingBgmControl
          variant="inline"
          src="/audio/games/shoot-them-all/Untitled.mp3"
          storageKey="bgm-volume:shoot-them-all"
        />
      </StaPausePanel>

      {/* 容器常驻挂载：z-60 只负责给结算浮层提供定位上下文。
          空壳时必须 pointer-events-none，否则选关卡点击与画布瞄准被整层拦截
          （真页面点击验收抓到的阻断级问题）；结算在场时恢复命中，让浮层自挡输入。 */}
      <div
        className={`fixed inset-0 z-[60] ${
          overlay === "result" && result ? "" : "pointer-events-none"
        }`}
      >
        <AnimatePresence>
          {overlay === "result" && result ? (
            <StaResult
              key="result"
              data={result}
              isLastLevel={lastLevel}
              onNext={() => next(result.levelId)}
              onRetry={retry}
              onExit={goSelect}
            />
          ) : null}
        </AnimatePresence>
      </div>

      <GameBackButton variant="floating" />
    </MotionConfig>
  )
}
