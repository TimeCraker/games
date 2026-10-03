"use client"

import dynamic from "next/dynamic"
import React, { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { useRouter } from "next/navigation"
import { ChevronRight } from "lucide-react"
import { cinematicEase } from "@/src/lib/motion"
import { onIdle } from "@/src/lib/idle"
import { LoopingBgmControl } from "@/src/components/audio/LoopingBgmControl"

const CinematicBlackHole = dynamic(
  () => import("@/src/components/CinematicBlackHole").then((m) => m.CinematicBlackHole),
  { ssr: false, loading: () => <div className="absolute inset-0 bg-black" /> },
)

export default function Home() {
  const router = useRouter()

  // 性能优化 2026-10：黑洞场景（three.js ~640KB chunk + WebGL 初始化）延后到浏览器空闲期。
  // 视觉无差：占位为同色纯黑（loading 兜底相同），页面本身的分阶段淡入（0.4s~1.4s）
  // 会先于/覆盖场景出现；快速网络下 idle 回调在 ~100-300ms 内触发，肉眼不可感知。
  // 收益：落地页关键路径腾出带宽给字体与首包（Slow 4G 下 LCP 11.3s 的主因是
  // 全屏 canvas 的首次绘制排在所有 JS 之后），TBT 同步下降。
  const [blackHoleReady, setBlackHoleReady] = useState(false)
  useEffect(() => onIdle(() => setBlackHoleReady(true), 2500), [])

  return (
    <div className="relative flex min-h-[100dvh] flex-col overflow-hidden bg-space-black text-white">
      {/* 背景:黑洞引力源(品牌资产) */}
      <motion.div
        className="pointer-events-none absolute inset-0 z-0"
        initial={{ opacity: 0, scale: 0.94 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.2, delay: 0.12, ease: cinematicEase }}
      >
        {blackHoleReady ? (
          <CinematicBlackHole
            interactive
            intensity={1}
            opacity={0.9}
            className="pointer-events-none absolute inset-0"
          />
        ) : (
          <div className="absolute inset-0 bg-black" />
        )}
      </motion.div>

      {/* 星图坐标网格(committed 视觉决策) */}
      <div className="star-chart-grid pointer-events-none absolute inset-0 z-[1]" />

      {/* 顶部观测台坐标栏 */}
      <motion.header
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: cinematicEase }}
        className="relative z-20 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6 sm:py-7"
      >
        <span className="font-mono-data text-[11px] uppercase tracking-[0.22em] text-white/50">
          AsterNova · Observatory
        </span>
        <span className="font-mono-data text-[11px] tracking-[0.14em] text-white/50">
          23h 17m · +41°
        </span>
      </motion.header>

      {/* 居中品牌 hero(高级排版:大字 + 留白 + 层次) */}
      <main id="main-content" tabIndex={-1} className="relative z-10 flex flex-1 flex-col items-center justify-center px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 18, filter: "blur(10px)" }}
          animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          transition={{ duration: 0.95, delay: 0.4, ease: cinematicEase }}
          className="space-y-7"
        >
          {/* 帽线图注（R7）：mono 双语 kicker，单一琥珀；窄屏收字号防中文断词 */}
          <div className="flex items-center justify-center gap-3">
            <span aria-hidden className="hidden h-px w-8 bg-hud-accent/45 sm:block sm:w-12" />
            <span className="whitespace-nowrap font-mono-data text-[9px] uppercase tracking-[0.2em] text-hud-accent/90 sm:text-[11px] sm:tracking-[0.28em]">
              Deep Space Observatory · 深空观测站
            </span>
            <span aria-hidden className="hidden h-px w-8 bg-hud-accent/45 sm:block sm:w-12" />
          </div>
          <h1 className="aster-title text-4xl sm:text-6xl md:text-7xl">ASTERNOVA STUDIO</h1>
          <p className="aster-slogan text-sm sm:text-base">Reach Beyond the Stars</p>
          <div className="mx-auto h-px w-24 bg-gradient-to-r from-transparent via-hud-accent/40 to-transparent" />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 1, ease: cinematicEase }}
          className="mt-12"
        >
          <motion.button
            type="button"
            onClick={() => router.push("/login")}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            transition={{ type: "spring", stiffness: 420, damping: 26 }}
            className="group relative inline-flex items-center rounded-full bg-white/[0.08] p-[3px] ring-1 ring-white/15 transition-[box-shadow,border-color] duration-300 hover:ring-hud-accent/40 hover:shadow-[0_10px_36px_-12px_rgba(216,163,60,0.4)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hud-accent/60"
          >
            {/* 双层壳：外圈半透明环 + 内芯纯白胶囊，琥珀箭头作唯一彩色点缀 */}
            <span className="inline-flex items-center gap-2 rounded-full bg-white px-9 py-3 text-sm font-semibold text-black shadow-[inset_0_1px_0_rgba(255,255,255,0.9)] transition-[filter] duration-200 ease-[var(--ease-instrument)] group-hover:brightness-[1.02]">
              <span>进入大厅</span>
              <ChevronRight className="h-4 w-4 text-hud-accent transition-transform duration-300 group-hover:translate-x-1" strokeWidth={2.25} />
            </span>
          </motion.button>
          <p className="font-mono-data mt-4 text-[10px] tracking-[0.12em] text-white/50">
            登录后进入游戏大厅 · ENTER THE LOBBY
          </p>
        </motion.div>
      </main>

      {/* 底部坐标 */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay: 1.4, ease: cinematicEase }}
        className="relative z-10 mx-auto w-full max-w-6xl px-6 pb-20 pt-6 sm:pb-7 sm:pt-7"
      >
        <p className="font-mono-data text-center text-[10px] tracking-[0.18em] text-white/50">
          © 2026 ASTERNOVA · DEEP SPACE OBSERVATORY
        </p>
      </motion.footer>

      {/* 性能优化 2026-10：落地页 BGM（1.4MB WAV）不再进加载关键路径——浏览器本就禁止
          无手势自动播放，preload=auto 的字节在用户第一次交互前纯属浪费，Slow 4G 下
          相当于 ~7s 的带宽争抢。首次 pointerdown 时 play() 会自动触发加载，听感无差。 */}
      <LoopingBgmControl
        src="/audio/home/Deep_space_ambient_d_#4-1774866771004.wav"
        storageKey="bgm-volume:home"
        deferLoadUntilGesture
      />
    </div>
  )
}
