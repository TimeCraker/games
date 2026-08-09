"use client"

import dynamic from "next/dynamic"
import { motion } from "framer-motion"
import { useRouter } from "next/navigation"
import { ChevronRight } from "lucide-react"
import { cinematicEase } from "@/src/lib/motion"
import { LoopingBgmControl } from "@/src/components/audio/LoopingBgmControl"

const CinematicBlackHole = dynamic(
  () => import("@/src/components/CinematicBlackHole").then((m) => m.CinematicBlackHole),
  { ssr: false, loading: () => <div className="absolute inset-0 bg-black" /> },
)

export default function Home() {
  const router = useRouter()

  return (
    <div className="relative flex min-h-[100dvh] flex-col overflow-hidden bg-space-black text-white">
      {/* 背景:黑洞引力源(品牌资产) */}
      <motion.div
        className="pointer-events-none absolute inset-0 z-0"
        initial={{ opacity: 0, scale: 0.94 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.2, delay: 0.12, ease: cinematicEase }}
      >
        <CinematicBlackHole
          interactive
          intensity={1}
          opacity={0.9}
          className="pointer-events-none absolute inset-0"
        />
      </motion.div>

      {/* 星图坐标网格(committed 视觉决策) */}
      <div className="star-chart-grid pointer-events-none absolute inset-0 z-[1]" />

      {/* 引力扫描:主时刻动效 */}
      <div className="pointer-events-none absolute inset-0 z-[2] overflow-hidden">
        <div className="gravity-scan-line absolute left-0 h-[42vh] w-full bg-[linear-gradient(to_bottom,transparent,rgba(56,189,248,0.09),transparent)]" />
      </div>

      {/* 顶部观测台坐标栏 */}
      <motion.header
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: cinematicEase }}
        className="relative z-20 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6 sm:py-7"
      >
        <span className="font-mono-data text-[11px] uppercase tracking-[0.22em] text-white/45">
          AsterNova · Observatory
        </span>
        <span className="font-mono-data text-[11px] tracking-[0.14em] text-white/35">
          23h 17m · +41°
        </span>
      </motion.header>

      {/* 居中品牌 hero(高级排版:大字 + 留白 + 层次) */}
      <main className="relative z-10 flex flex-1 flex-col items-center justify-center px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 18, filter: "blur(10px)" }}
          animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          transition={{ duration: 0.95, delay: 0.4, ease: cinematicEase }}
          className="space-y-7"
        >
          <h1 className="aster-title text-4xl sm:text-6xl md:text-7xl">ASTERNOVA STUDIO</h1>
          <p className="aster-slogan text-sm sm:text-base">Reach Beyond the Stars</p>
          <div className="mx-auto h-px w-24 bg-gradient-to-r from-transparent via-white/35 to-transparent" />
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
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            transition={{ type: "spring", stiffness: 420, damping: 26 }}
            className="group relative inline-flex items-center gap-2 rounded-full bg-white px-10 py-3.5 text-sm font-semibold text-black shadow-[inset_0_1px_0_rgba(255,255,255,0.6)] transition-shadow duration-300 hover:bg-white/90 hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.6),0_8px_30px_-8px_rgba(255,255,255,0.3)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
          >
            <span>进入大厅</span>
            <ChevronRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" strokeWidth={2} />
          </motion.button>
          <p className="font-mono-data mt-4 text-[10px] tracking-[0.12em] text-white/30">
            登录后进入游戏大厅
          </p>
        </motion.div>
      </main>

      {/* 底部坐标 */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay: 1.4, ease: cinematicEase }}
        className="relative z-10 mx-auto w-full max-w-6xl px-6 py-6 sm:py-7"
      >
        <p className="font-mono-data text-center text-[10px] tracking-[0.18em] text-white/25">
          © 2026 ASTERNOVA · DEEP SPACE OBSERVATORY
        </p>
      </motion.footer>

      <LoopingBgmControl src="/audio/home/Deep_space_ambient_d_#4-1774866771004.wav" storageKey="bgm-volume:home" />
    </div>
  )
}
