"use client"

import { motion } from "framer-motion"
import { useRouter } from "next/navigation"

import { CinematicBlackHole } from "@/src/components/CinematicBlackHole"
import { LoopingBgmControl } from "@/src/components/audio/LoopingBgmControl"

const cinematicEase = [0.22, 1, 0.36, 1] as const

export default function Home() {
  const router = useRouter()

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-transparent text-white">
      <style>{`
        .aster-title {
          background: linear-gradient(120deg, rgba(56,189,248,0.95), rgba(168,85,247,0.95), rgba(99,102,241,0.95));
          -webkit-background-clip: text;
          background-clip: text;
          color: transparent;
        }
        .aster-slogan {
          color: rgba(255,255,255,0.55);
          text-shadow: 0 0 14px rgba(255,255,255,0.06);
        }
      `}</style>

      <motion.div
        className="pointer-events-none absolute inset-0 z-0 bg-black"
        initial={{ opacity: 1 }}
        animate={{ opacity: 0 }}
        transition={{ duration: 0.36, ease: cinematicEase }}
      />

      <motion.div
        className="pointer-events-none absolute inset-0"
        initial={{ opacity: 0, scale: 0.94 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.15, delay: 0.12, ease: cinematicEase }}
      >
        <CinematicBlackHole
          interactive
          intensity={1}
          opacity={0.9}
          className="pointer-events-none absolute inset-0"
        />
      </motion.div>

      <motion.div
        className="pointer-events-none absolute left-1/2 top-1/2 z-[1] h-[62vmin] w-[62vmin] -translate-x-1/2 -translate-y-1/2 rounded-full"
        initial={{ opacity: 0, scale: 0.96, rotate: -10 }}
        animate={{ opacity: 1, scale: 1, rotate: 0 }}
        transition={{ duration: 1.18, delay: 0.2, ease: cinematicEase }}
      >
        <motion.div
          className="absolute inset-0 rounded-full border border-violet-300/25"
          style={{
            background:
              "conic-gradient(from 220deg, rgba(255,182,193,0.0), rgba(255,182,193,0.45), rgba(168,85,247,0.38), rgba(96,165,250,0.0))",
            maskImage: "radial-gradient(circle, transparent 66%, black 73%, transparent 79%)",
            WebkitMaskImage: "radial-gradient(circle, transparent 66%, black 73%, transparent 79%)",
            filter: "blur(1.2px)",
          }}
          initial={{ opacity: 0.1, rotate: -45 }}
          animate={{ opacity: [0.4, 0.64, 0.46], rotate: [0, 6, 0] }}
          transition={{ duration: 1.22, delay: 0.28, ease: cinematicEase }}
        />
      </motion.div>

      <motion.div
        className="pointer-events-none absolute inset-0 z-[1]"
        animate={{ opacity: [0.12, 0.2, 0.12] }}
        transition={{ duration: 4.8, repeat: Infinity, ease: "easeInOut" }}
        style={{
          background:
            "radial-gradient(circle at 50% 48%, rgba(168,85,247,0.16), rgba(56,189,248,0.08) 34%, rgba(0,0,0,0) 62%)",
        }}
      />

      <motion.div
        className="relative z-10 flex w-full max-w-4xl flex-col items-center px-6 text-center"
        initial={{ opacity: 0, y: 20, filter: "blur(8px)" }}
        animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
        transition={{ duration: 0.85, delay: 0.9, ease: cinematicEase }}
      >
        <div className="mt-[46vh] sm:mt-[48vh]" />

        <motion.h1
          className="aster-title text-3xl font-semibold tracking-[0.22em] sm:text-4xl"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 1.02, ease: cinematicEase }}
        >
          ASTERNOVA STUDIO
        </motion.h1>
        <motion.p
          className="aster-slogan mt-3 text-sm sm:text-base"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 1.12, ease: cinematicEase }}
        >
          Reach Beyond the Stars
        </motion.p>

        <motion.div
          className="mt-8"
          initial={{ opacity: 0, y: 10, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.72, delay: 1.22, ease: cinematicEase }}
        >
          <motion.button
            type="button"
            onClick={() => router.push("/login")}
            className="group relative inline-flex items-center justify-center rounded-full bg-gradient-to-r from-cyan-300 via-violet-400 to-indigo-400 px-10 py-3 text-sm font-semibold text-black shadow-[0_0_44px_rgba(168,85,247,0.25)] transition duration-300 hover:scale-[1.03] hover:shadow-[0_0_70px_rgba(56,189,248,0.30)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-200"
            whileTap={{ scale: 0.985 }}
            transition={{ type: "spring", stiffness: 420, damping: 26 }}
          >
            <span className="relative z-10 flex items-center gap-2">
              <span className="text-[0.95rem]">开始自由探索（登录Login）</span>
              <span className="mt-[1px] text-xs opacity-80">↗</span>
            </span>
            <span className="pointer-events-none absolute inset-[1px] rounded-full bg-black/10 transition group-hover:bg-black/15" />
            <span className="pointer-events-none absolute inset-0 rounded-full bg-[linear-gradient(120deg,rgba(255,255,255,0.0),rgba(255,255,255,0.32),rgba(255,255,255,0.0))] opacity-0 blur-[1px] transition duration-500 group-hover:opacity-100 group-hover:translate-x-1" />
          </motion.button>
        </motion.div>
      </motion.div>
      <LoopingBgmControl src="/audio/home/Deep_space_ambient_d_#4-1774866771004.wav" storageKey="bgm-volume:home" />
    </div>
  )
}
