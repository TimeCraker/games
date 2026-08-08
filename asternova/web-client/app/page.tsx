"use client"

import dynamic from "next/dynamic"
import { motion } from "framer-motion"
import { useRouter } from "next/navigation"
import { ChevronRight, Footprints, Gem, Layers, Orbit, Target } from "lucide-react"
import { cinematicEase } from "@/src/lib/motion"
import { LoopingBgmControl } from "@/src/components/audio/LoopingBgmControl"

const CinematicBlackHole = dynamic(
  () => import("@/src/components/CinematicBlackHole").then((m) => m.CinematicBlackHole),
  { ssr: false, loading: () => <div className="absolute inset-0 bg-black" /> },
)

const GAMES = [
  { href: "/shoot-them-all", category: "Physics", title: "Shoot Them All", blurb: "物理弹射 · 连锁清场", Icon: Target },
  { href: "/lets-running", category: "Runner", title: "Let's Running", blurb: "Star Dash · 跑酷滑铲", Icon: Footprints },
  { href: "/merge", category: "Merge", title: "AsterNova Merge", blurb: "合成星球 · 十级进化", Icon: Layers },
  { href: "/nebula-survivor", category: "Survivor", title: "Nebula Survivor", blurb: "俯视角肉鸽 · 构筑", Icon: Orbit },
  { href: "/xiaoxiaole", category: "Match-3", title: "桓睿消消乐", blurb: "立体三消 · 12关闯关", Icon: Gem },
] as const

export default function Home() {
  const router = useRouter()

  return (
    <div className="relative min-h-[100dvh] overflow-hidden bg-[#05030f] text-white">
      {/* 背景:黑洞引力源(品牌资产保留) */}
      <motion.div
        className="pointer-events-none absolute inset-0 z-0"
        initial={{ opacity: 0, scale: 0.94 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.15, delay: 0.12, ease: cinematicEase }}
      >
        <CinematicBlackHole
          interactive
          intensity={1}
          opacity={0.85}
          className="pointer-events-none absolute inset-0"
        />
      </motion.div>

      {/* 星图坐标网格(committed 视觉决策,贯穿全站) */}
      <div className="star-chart-grid pointer-events-none absolute inset-0 z-[1]" />

      {/* 引力扫描:主时刻动效(一个精心设计,非散布) */}
      <div className="pointer-events-none absolute inset-0 z-[2] overflow-hidden">
        <div className="gravity-scan-line absolute left-0 h-[42vh] w-full bg-[linear-gradient(to_bottom,transparent,rgba(56,189,248,0.09),transparent)]" />
      </div>

      {/* 顶部观测台导航 */}
      <motion.header
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: cinematicEase }}
        className="relative z-20 mx-auto flex max-w-6xl items-center justify-between px-4 py-5 sm:px-6"
      >
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/15 bg-white/[0.06]">
            <Orbit className="h-4 w-4 text-white/80" strokeWidth={1.7} />
          </div>
          <span className="font-mono-data text-[11px] uppercase tracking-[0.2em] text-white/45">
            AsterNova · Obs
          </span>
        </div>
        <span className="font-mono-data text-[11px] tracking-[0.12em] text-white/35">
          23h 17m · +41°
        </span>
      </motion.header>

      {/* Hero:Orbitron 非渐变标题(craft 禁忌修复) */}
      <motion.section
        initial={{ opacity: 0, y: 16, filter: "blur(8px)" }}
        animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
        transition={{ duration: 0.8, delay: 0.3, ease: cinematicEase }}
        className="relative z-10 mx-auto max-w-6xl px-4 pt-4 text-center sm:px-6 sm:pt-8"
      >
        <h1 className="aster-title text-3xl sm:text-5xl">ASTERNOVA STUDIO</h1>
        <p className="aster-slogan mt-3 text-sm sm:text-base">Reach Beyond the Stars</p>
        <p className="font-mono-data mx-auto mt-5 max-w-md text-[11px] leading-relaxed tracking-[0.06em] text-white/40">
          即刻进入的宇宙游戏矩阵 · 五款休闲小游戏 + 联机战场
        </p>
      </motion.section>

      {/* 游戏矩阵:首屏即论点(可即刻进入,证明而非声称) */}
      <motion.section
        initial="hidden"
        animate="show"
        variants={{
          hidden: {},
          show: { transition: { staggerChildren: 0.07, delayChildren: 0.6 } },
        }}
        className="relative z-10 mx-auto max-w-6xl px-4 py-9 sm:px-6 sm:py-12"
      >
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-5">
          {GAMES.map((g) => (
            <motion.button
              key={g.href}
              type="button"
              variants={{
                hidden: { opacity: 0, y: 18 },
                show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: cinematicEase } },
              }}
              whileHover={{ y: -4 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => router.push(g.href)}
              className="observation-window group relative flex flex-col overflow-hidden rounded-2xl border border-white/[0.08] p-4 text-left transition-colors duration-300 hover:border-violet-400/30 focus-visible:border-violet-400/50 focus-visible:outline-none"
            >
              <div className="flex items-center justify-between">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-white/[0.05]">
                  <g.Icon className="h-[1.1rem] w-[1.1rem] text-white/85" strokeWidth={1.7} />
                </div>
                <span className="font-mono-data text-[9px] uppercase tracking-[0.14em] text-white/35">
                  {g.category}
                </span>
              </div>
              <p className="mt-4 text-[14px] font-semibold leading-snug tracking-[-0.01em] text-white">
                {g.title}
              </p>
              <p className="mt-1 text-[12px] leading-snug text-white/45">{g.blurb}</p>
              <span className="mt-3 inline-flex items-center gap-1 text-[11px] font-medium text-violet-300/70 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                即玩 <ChevronRight className="h-3 w-3" strokeWidth={2.5} />
              </span>
            </motion.button>
          ))}
        </div>
      </motion.section>

      {/* 底部 CTA:登录进大厅(非发光边,刻度玻璃) */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 1, ease: cinematicEase }}
        className="relative z-10 mx-auto max-w-6xl px-4 pb-12 text-center sm:px-6"
      >
        <motion.button
          type="button"
          onClick={() => router.push("/login")}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          transition={{ type: "spring", stiffness: 420, damping: 26 }}
          className="group relative inline-flex items-center gap-2 rounded-full border border-violet-400/30 bg-violet-500/10 px-8 py-3 text-sm font-semibold text-white backdrop-blur-sm transition-colors duration-300 hover:border-violet-400/50 hover:bg-violet-500/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400/40"
        >
          <span>进入大厅 · 登录</span>
          <ChevronRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" strokeWidth={2} />
        </motion.button>
        <p className="font-mono-data mt-3 text-[10px] tracking-[0.1em] text-white/30">
          登录后解锁联机战场与匹配
        </p>
      </motion.div>

      <LoopingBgmControl src="/audio/home/Deep_space_ambient_d_#4-1774866771004.wav" storageKey="bgm-volume:home" />
    </div>
  )
}
