"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { Orbitron } from "next/font/google"

import { CinematicBlackHole } from "@/src/components/CinematicBlackHole"
import { LoopingBgmControl } from "@/src/components/audio/LoopingBgmControl"
import { apiV1BaseUrl } from "@/src/config/public-env"
import { useMobileGameViewport } from "@/src/hooks/useMobileGameViewport"
import { useGameStore } from "@/src/store/useGameStore"

const orbitron = Orbitron({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
})

export default function ArenaPage() {
  const router = useRouter()
  const iframeRef = React.useRef<HTMLIFrameElement>(null)
  const [isSceneReady, setIsSceneReady] = React.useState(false)
  const [p1Status, setP1Status] = React.useState({ hp: 100, energy: 0 })
  const [p2Status, setP2Status] = React.useState({ hp: 100, energy: 0 })
  const [countdown, setCountdown] = React.useState<number | string | null>(null)
  const [loadingProgress, setLoadingProgress] = React.useState(8)
  // ===== 新增代码 START =====
  // 修改内容：新增对局结算状态，用于控制结算遮罩 UI
  // 修改原因：需要在收到 Godot 的 game_over 后展示胜负并保持 4 秒后回大厅
  // 影响范围：仅渲染层状态与 UI，不影响网络/路由逻辑
  const [matchResult, setMatchResult] = React.useState<'victory' | 'defeat' | null>(null)
  // ===== 新增代码 END =====

  const token = useGameStore((s) => s.token)
  const userId = useGameStore((s) => s.userId)
  // ===== 新增代码 START =====
  const username = useGameStore((s) => s.username)
  // ===== 新增代码 END =====
  const currentRoomId = useGameStore((s) => s.currentRoomId)
  const selectedClass = useGameStore((s) => s.selectedClass)
  const sessionReadyForBattle = useGameStore((s) => s.sessionReadyForBattle)

  const { isMobile, shouldShowLandscapeHint } = useMobileGameViewport()

  const canEnterArena = Boolean(token && userId && currentRoomId && sessionReadyForBattle)

  // 严格安全的路由守卫：逃跑惩罚与断线踢出
  React.useEffect(() => {
    // 1. 刷新惩罚：没有 sessionReadyForBattle 通行证（玩家按了刷新）
    if (!sessionReadyForBattle) {
      const state = useGameStore.getState()
      state.clearAuth() // 严厉惩罚：彻底清空 Token 和 userId
      state.setCurrentRoomId("")
      toast.error("检测到战斗中刷新，判定为逃跑。已清空身份，请重新登录！")
      router.replace("/login") // 直接踢回登录页
      return
    }

    // 2. 状态丢失：有通行证，但 Token 意外丢失
    if (!canEnterArena) {
      toast.error("战场会话已失效，请重新登录")
      useGameStore.getState().clearAuth()
      router.replace("/login")
    }
  }, [sessionReadyForBattle, canEnterArena, router])

  const handleGodotLoad = React.useCallback(() => {
    if (!iframeRef.current || !iframeRef.current.contentWindow) return
    // 永久治本方案：直接用 React 潜入 iframe 内部，把 Godot 的加载条给删掉！
    try {
      const iframeDoc = iframeRef.current.contentDocument || iframeRef.current.contentWindow.document
      if (iframeDoc) {
        const style = iframeDoc.createElement("style")
        style.innerHTML = "#status { display: none !important; } canvas { background-color: transparent !important; }"
        iframeDoc.head.appendChild(style)
        console.log("[ArenaPage] 已成功向 Godot 注入静默样式")
      }
    } catch (err) {
      console.warn("[ArenaPage] 无法修改 iframe 内部样式 (可能跨域)", err)
    }

    // ===== 新增代码 START =====
    type EnterBattlePayload = {
      token: string
      userId: number
      username: string
      roomId: string
      selectedClass: string
      wsBase: string
      isMobile: boolean
    }
    // ===== 新增代码 END =====
    const payload: EnterBattlePayload = {
      token,
      userId,
      // ===== 新增代码 START =====
      username,
      // ===== 新增代码 END =====
      roomId: currentRoomId,
      selectedClass,
      wsBase: process.env.NEXT_PUBLIC_WS_URL ?? "",
      isMobile,
    }

    // 使用轮询等待 Godot 引擎初始化并挂载方法
    const tryInject = () => {
      const cw = iframeRef.current?.contentWindow as (Window & { enterBattle?: (json: string) => void }) | null
      if (cw && typeof cw.enterBattle === "function") {
        try {
          cw.enterBattle(JSON.stringify(payload))
          console.log("[ArenaPage] 已向 Godot 注入战场参数")
        } catch (err) {
          console.error("[ArenaPage] 向 Godot 注入参数失败:", err)
        }
      } else {
        // 如果还没有挂载上，等待 100ms 后重试
        setTimeout(tryInject, 100)
      }
    }

    tryInject()
  }, [token, userId, username, currentRoomId, selectedClass, isMobile])

  React.useEffect(() => {
    const handleBattleResult = (event: Event) => {
      const customEvent = event as CustomEvent<{ resultType?: string; payload?: unknown }>
      const { resultType = "", payload } = customEvent.detail ?? {}

      if (resultType === "engine_ready") {
        setIsSceneReady(true)
        return
      }

      if (resultType === "player_status") {
        try {
          const data =
            typeof payload === "string"
              ? (JSON.parse(payload as string) as { is_local: boolean; hp: number; energy: number })
              : (payload as { is_local: boolean; hp: number; energy: number })
          if (data.is_local) {
            setP1Status({ hp: data.hp, energy: data.energy })
          } else {
            setP2Status({ hp: data.hp, energy: data.energy })
          }
        } catch (e) {
          console.error("解析状态失败", e)
        }
        return
      }

      // ===== 新增代码 START =====
      // 修改内容：拦截 Godot 发来的 game_over 信号，驱动结算 UI 并在演出结束后回大厅
      // 修改原因：与后端的 game_over 广播对齐，确保慢动作结束后把胜负结果推给 React
      // 影响范围：仅当 resultType === "game_over" 时中断默认 toast + router 行为
      if (resultType === "game_over") {
        try {
          const data = typeof payload === "string" ? JSON.parse(payload) : payload
          const winnerId = (data as { winner_id?: number | string }).winner_id
          const isVictory = Number(winnerId) === userId
          setMatchResult(isVictory ? "victory" : "defeat")

          // 停留 4 秒让玩家装 X，然后自动退回大厅
          setTimeout(() => {
            router.replace("/lobby")
          }, 4000)
        } catch (e) {
          console.error("解析结算失败", e)
        }
        return
      }
      // ===== 新增代码 END =====

      console.log("收到 Godot 战斗结果:", resultType, payload)

      if (resultType === "win" || resultType === "victory" || resultType === "opponent_left") {
        toast.success("对局结束：对手离线，你已获胜")
      } else if (resultType) {
        toast.info(`对局结束：${resultType}`)
      } else {
        toast.info("对局结束")
      }

      router.replace("/lobby")
    }

    window.addEventListener("unity:battle_result", handleBattleResult)
    return () => window.removeEventListener("unity:battle_result", handleBattleResult)
  }, [router])

  React.useEffect(() => {
    if (isSceneReady) {
      setLoadingProgress(100)
      return
    }
    const timer = window.setInterval(() => {
      setLoadingProgress((prev) => {
        if (prev >= 92) return prev
        const step = prev < 40 ? 4 : prev < 72 ? 2 : 1
        return Math.min(92, prev + step)
      })
    }, 240)
    return () => window.clearInterval(timer)
  }, [isSceneReady])

  React.useEffect(() => {
    if (isSceneReady) {
      setCountdown(3)
      let count = 3
      const interval = setInterval(() => {
        count -= 1
        if (count > 0) {
          setCountdown(count)
        } else if (count === 0) {
          setCountdown("FIGHT!")
          // 呼叫 Godot 解除玩家冻结
          try {
            const cw = iframeRef.current?.contentWindow as any
            cw?.startFight?.()
          } catch (e) {}
        } else {
          setCountdown(null)
          clearInterval(interval)
        }
      }, 1000)
      return () => clearInterval(interval)
    }
  }, [isSceneReady])

  React.useEffect(() => {
    if (!canEnterArena) return
    const onBeforeUnload = () => {
      const { token: t, currentRoomId: rid } = useGameStore.getState()
      if (t && rid) {
        try {
          const blob = new Blob([JSON.stringify({ roomId: rid, reason: "page_unload" })], { type: "application/json" })
          navigator.sendBeacon(`${apiV1BaseUrl}/battle_forfeit`, blob)
        } catch {}
      }
    }
    window.addEventListener("beforeunload", onBeforeUnload)

    // 关键修正：坚决不在这里重置 sessionReadyForBattle！全权交给内存生命周期自然销毁
    return () => {
      window.removeEventListener("beforeunload", onBeforeUnload)
    }
  }, [canEnterArena])

  if (!canEnterArena) {
    return null
  }

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-black text-white">
      {shouldShowLandscapeHint && (
        <div
          className="absolute inset-0 z-[200] flex flex-col items-center justify-center gap-6 bg-black/92 px-8 text-center backdrop-blur-md"
          role="dialog"
          aria-live="polite"
          aria-label="请横屏游戏"
        >
          <div
            className={[orbitron.className, "max-w-md text-lg font-semibold leading-relaxed text-cyan-100/95"].join(" ")}
            style={{ textShadow: "0 0 24px rgba(34,211,238,0.35)" }}
          >
            为了获得最佳游戏体验，请关闭系统的屏幕旋转锁定，并将手机横置。
          </div>
          <div className="text-sm text-white/55">横屏后即可继续战斗</div>
        </div>
      )}
      <style
        dangerouslySetInnerHTML={{
          __html: `
            @keyframes wave-move {
              0% { mask-position-x: 0%; -webkit-mask-position-x: 0%; }
              100% { mask-position-x: 200%; -webkit-mask-position-x: 200%; }
            }
            .wave-move-anim {
              mask-size: 100% 100%; -webkit-mask-size: 100% 100%;
              animation: wave-move 3s linear infinite !important;
            }
          `,
        }}
      />
      <CinematicBlackHole interactive={false} intensity={0.95} opacity={0.3} className="pointer-events-none absolute inset-0" />

      <div
        className={`absolute inset-0 h-full w-full transition-opacity duration-1000 ${isSceneReady ? "opacity-100" : "opacity-0 pointer-events-none"}`}
      >
        <iframe
          ref={iframeRef}
          src="/godot/GoDot_game.html"
          className="w-full h-full border-none outline-none"
          onLoad={handleGodotLoad}
        />
      </div>

      {!isSceneReady && (
        <div className="relative z-10 flex h-full w-full items-center justify-center">
          <div className="w-full max-w-2xl px-6">
            <div className="mx-auto rounded-[28px] border border-white/20 bg-[linear-gradient(155deg,rgba(255,255,255,0.16),rgba(255,255,255,0.03))] p-8 shadow-[0_0_0_1px_rgba(255,255,255,0.12),0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur-2xl">
              <div className={[orbitron.className, "text-center"].join(" ")}>
                <div className="text-[11px] tracking-[0.38em] text-white/55">ASTER NOVA</div>
                <div className="mt-3 text-2xl font-semibold tracking-tight text-white drop-shadow-[0_0_24px_rgba(255,255,255,0.14)]">
                  正在进入战场
                </div>
                <div className="mt-3 text-sm text-white/68">
                  {loadingProgress < 35
                    ? "同步战场会话..."
                    : loadingProgress < 70
                      ? "加载地图与资源..."
                      : "连接对战引擎..."}
                </div>

                <div className="mx-auto mt-6 w-full max-w-xl">
                  <div className="h-2.5 overflow-hidden rounded-full border border-white/20 bg-white/10">
                    <div
                      className="h-full rounded-full bg-[linear-gradient(90deg,rgba(255,255,255,0.85),rgba(167,243,208,0.92),rgba(147,197,253,0.9))] transition-[width] duration-300 ease-out"
                      style={{ width: `${loadingProgress}%`, boxShadow: "0 0 24px rgba(167,243,208,0.35)" }}
                    />
                  </div>
                  <div className="mt-2 flex items-center justify-between text-[11px] tracking-[0.14em] text-white/55">
                    <span>PREPARING</span>
                    <span>{loadingProgress}%</span>
                  </div>
                </div>

                <div className="mx-auto mt-5 h-px w-full max-w-xl bg-gradient-to-r from-transparent via-white/30 to-transparent" />
                <div className="mt-4 text-xs text-white/55">建议保持当前页面，加载完成后将自动开始</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {countdown && (
        <div className="pointer-events-none absolute inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm transition-all duration-300">
          <div
            key={countdown}
            className={[
              orbitron.className,
              "animate-in zoom-in-50 fade-in duration-500 text-[10rem] font-black italic tracking-tighter text-transparent",
            ].join(" ")}
            style={{
              WebkitTextStroke: "2px rgba(255,255,255,0.8)",
              backgroundImage: "linear-gradient(to bottom right, #f9a8d4, #a855f7, #67e8f9)",
              WebkitBackgroundClip: "text",
              filter: "drop-shadow(0 0 40px rgba(168,85,247,0.6))",
            }}
          >
            {countdown}
          </div>
        </div>
      )}

      {isSceneReady && (
        <>
          {/* 大招 Q 按键 (赛博液体波纹 - 绝对防御级内联样式) */}
          <div
            className="absolute left-4 top-24 z-50 flex items-center justify-center pointer-events-none transition-all duration-300"
            style={{
              width: "72px",
              height: "72px",
              filter: p1Status.energy >= 15 ? "drop-shadow(0 0 25px rgba(236,72,153,0.95))" : "drop-shadow(0 0 8px rgba(0,0,0,0.7))",
              scale: p1Status.energy >= 15 ? "1.15" : "1.0",
            }}
          >
            <div style={{ position: "absolute", inset: 0, borderRadius: "999px", border: "3px solid rgba(255,255,255,0.3)", backgroundColor: "rgba(0,0,0,0.85)", boxShadow: "inset 0 0 15px rgba(236,72,153,0.3)", backdropFilter: "blur(8px)" }} />

            <div style={{ position: "absolute", inset: "4px", overflow: "hidden", borderRadius: "999px" }}>
              <div
                className="wave-move-anim"
                style={{
                  position: "absolute",
                  left: "-50%",
                  width: "200%",
                  bottom: "-25%",
                  height: "100%",
                  backgroundImage: "linear-gradient(to top right, #f472b6, #60a5fa)",
                  transform: `translateY(-${(p1Status.energy / 15) * 100}%)`,
                  transition: "transform 0.3s ease-out, opacity 0.3s",
                  opacity: p1Status.energy >= 15 ? "1" : "0.7",
                  maskImage: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 1200 120\' preserveAspectRatio=\'none\'%3E%3Cpath d=\'M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V120H282.65C297.82,95.68,307.39,73.19,321.39,56.44Z\' style=\'fill:%23000;\'%3E%3C/path%3E%3C/svg%3E")',
                  WebkitMaskImage: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 1200 120\' preserveAspectRatio=\'none\'%3E%3Cpath d=\'M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V120H282.65C297.82,95.68,307.39,73.19,321.39,56.44Z\' style=\'fill:%23000;\'%3E%3C/path%3E%3C/svg%3E")',
                  maskRepeat: "repeat-x",
                  WebkitMaskRepeat: "repeat-x",
                }}
              />
            </div>

            <span
              className={[orbitron.className, "absolute z-10 text-5xl font-black italic"].join(" ")}
              style={{
                color: "#fff",
                transform: "translateY(1px)",
                filter: p1Status.energy >= 15 ? "drop-shadow(0 0 15px rgba(255,255,255,0.9))" : "drop-shadow(0 0 2px rgba(255,255,255,0.4))",
              }}
            >
              Q
            </span>
          </div>

          {/* P1 本地玩家 (左上角，往下挪一点) */}
          <div className="pointer-events-none absolute left-28 top-28 z-40 flex w-[40vw] max-w-[450px] flex-col gap-2">
            <div className="flex items-end justify-between px-2" style={{ textShadow: "0 0 8px rgba(0,0,0,0.8)" }}>
              <span className={[orbitron.className, "text-2xl font-black tracking-widest text-white"].join(" ")}>{username || "PLAYER 1"}</span>
              <span className={[orbitron.className, "text-sm font-bold tracking-widest text-yellow-400 drop-shadow-md"].join(" ")}>
                {p1Status.energy >= 15 ? "ULTIMATE READY [Q]" : "ENERGY"}
              </span>
            </div>
            {/* P1 主血条 */}
            <div
              style={{
                height: "28px",
                width: "100%",
                transform: "skewX(-12deg)",
                overflow: "hidden",
                borderRadius: "4px",
                border: "2px solid rgba(255,255,255,0.3)",
                backgroundColor: "rgba(0,0,0,0.8)",
                boxShadow: "0 0 15px rgba(0,0,0,0.8)",
                backdropFilter: "blur(12px)",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${p1Status.hp}%`,
                  backgroundImage: "linear-gradient(to right, #db2777, #f43f5e)",
                  transition: "width 0.3s ease-out",
                }}
              />
            </div>
            {/* P1 能量条 */}
            <div
              style={{
                height: "12px",
                width: "100%",
                transform: "skewX(-12deg)",
                overflow: "hidden",
                borderRadius: "4px",
                border: "1px solid rgba(255,255,255,0.2)",
                backgroundColor: "rgba(0,0,0,0.8)",
                boxShadow: "0 0 10px rgba(0,0,0,0.8)",
                backdropFilter: "blur(12px)",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${(p1Status.energy / 15) * 100}%`,
                  backgroundImage: "linear-gradient(to right, #facc15, #22d3ee)",
                  transition: "width 0.3s ease-out",
                }}
              />
            </div>
          </div>

          {/* P2 敌方玩家 (右上角) */}
          <div className="pointer-events-none absolute right-6 top-20 z-50 flex w-[40vw] max-w-[450px] flex-col items-end gap-2">
            <div className="flex w-full flex-row-reverse items-end justify-between px-2" style={{ textShadow: "0 0 8px rgba(0,0,0,0.8)" }}>
              <span className={[orbitron.className, "text-2xl font-black tracking-widest text-red-400"].join(" ")}>ENEMY</span>
            </div>
            {/* P2 主血条 */}
            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                height: "28px",
                width: "100%",
                transform: "skewX(12deg)",
                overflow: "hidden",
                borderRadius: "4px",
                border: "2px solid rgba(255,255,255,0.3)",
                backgroundColor: "rgba(0,0,0,0.8)",
                boxShadow: "0 0 15px rgba(0,0,0,0.8)",
                backdropFilter: "blur(12px)",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${p2Status.hp}%`,
                  backgroundImage: "linear-gradient(to left, #dc2626, #f97316)",
                  transition: "width 0.3s ease-out",
                }}
              />
            </div>
            {/* P2 能量条 */}
            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                height: "12px",
                width: "100%",
                transform: "skewX(12deg)",
                overflow: "hidden",
                borderRadius: "4px",
                border: "1px solid rgba(255,255,255,0.2)",
                backgroundColor: "rgba(0,0,0,0.8)",
                boxShadow: "0 0 10px rgba(0,0,0,0.8)",
                backdropFilter: "blur(12px)",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${(p2Status.energy / 15) * 100}%`,
                  backgroundImage: "linear-gradient(to left, #facc15, #22d3ee)",
                  transition: "width 0.3s ease-out",
                }}
              />
            </div>
          </div>
        </>
      )}

      {/* ===== 新增代码 START ===== */}
      {/* 修改内容：全屏赛博结算遮罩层（仅展示，不改变计时/跳转逻辑） */}
      {matchResult && (
        <div className="absolute inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm animate-in fade-in duration-1000">
          <div
            className={[orbitron.className, "relative flex flex-col items-center gap-6"].join(" ")}
            style={{
              padding: "2.2rem 2.4rem",
              borderRadius: 24,
              border: "1px solid rgba(255,255,255,0.12)",
              background:
                matchResult === "victory"
                  ? "radial-gradient(1000px 420px at 50% 40%, rgba(34,211,238,0.25), rgba(0,0,0,0) 60%), rgba(0,0,0,0.35)"
                  : "radial-gradient(1000px 420px at 50% 40%, rgba(220,38,38,0.22), rgba(0,0,0,0) 60%), rgba(0,0,0,0.35)",
              boxShadow:
                matchResult === "victory"
                  ? "0 0 60px rgba(34,211,238,0.20), inset 0 0 0 1px rgba(255,255,255,0.08)"
                  : "0 0 60px rgba(220,38,38,0.18), inset 0 0 0 1px rgba(255,255,255,0.08)",
            }}
          >
            {/* 背景扫描线 */}
            <div className="pointer-events-none absolute inset-0 rounded-[24px] overflow-hidden" aria-hidden="true">
              <div
                className="absolute inset-0"
                style={{
                  background:
                    "repeating-linear-gradient(to bottom, rgba(255,255,255,0.08), rgba(255,255,255,0.08) 1px, rgba(0,0,0,0) 3px, rgba(0,0,0,0) 6px)",
                  opacity: 0.25,
                  mixBlendMode: "overlay",
                }}
              />
              <div
                className="absolute left-0 right-0 h-1/3"
                style={{
                  top: "25%",
                  background: matchResult === "victory" ? "rgba(34,211,238,0.25)" : "rgba(220,38,38,0.22)",
                  filter: "blur(14px)",
                  transform: "translateY(0)",
                  animation: "pulse-scan 1.8s ease-in-out infinite",
                }}
              />
              <style
                dangerouslySetInnerHTML={{
                  __html: `
                    @keyframes pulse-scan {
                      0% { transform: translateY(-12%); opacity: 0.55; }
                      50% { transform: translateY(26%); opacity: 0.90; }
                      100% { transform: translateY(-12%); opacity: 0.55; }
                    }
                  `,
                }}
              />
            </div>

            <div className="relative">
              <div
                className={`text-[6.6rem] font-black italic tracking-widest ${
                  matchResult === "victory"
                    ? "text-cyan-400 drop-shadow-[0_0_50px_rgba(34,211,238,0.8)]"
                    : "text-red-600 drop-shadow-[0_0_50px_rgba(220,38,38,0.8)]"
                }`}
              >
                {matchResult === "victory" ? "VICTORY" : "DEFEAT"}
              </div>
              <div className="mt-4 h-1 w-96 bg-gradient-to-r from-transparent via-white/40 to-transparent" />
            </div>

            <div className="relative flex flex-col items-center gap-3">
              <div
                className="text-sm font-bold tracking-[0.45em] text-white/70 animate-pulse"
                style={{ textShadow: "0 0 18px rgba(255,255,255,0.15)" }}
              >
                RETURNING TO LOBBY...
              </div>
              <div
                className="h-[2px] w-72 bg-gradient-to-r from-transparent via-white/60 to-transparent"
                style={{ opacity: 0.55 }}
              />
              <div className="text-xs text-white/55 tracking-wide">
                你看到慢动作不是bug，是结算特效
              </div>
            </div>
          </div>
        </div>
      )}
      {/* ===== 新增代码 END ===== */}
      <LoopingBgmControl src="/audio/games/arena/Untitled.mp3" storageKey="bgm-volume:arena" />
    </div>
  )
}