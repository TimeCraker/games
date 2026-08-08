"use client"

import { useState } from "react"
import { AnimatePresence, motion } from "framer-motion"

import { FluidBlob } from "@/src/components/FluidBlob"

const easeOutExpo = [0.22, 1, 0.36, 1] as const

export function ElevenLabsTransitionDemo() {
  const [isSubmitted, setIsSubmitted] = useState(false)

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#08070c] px-6 py-10 text-white">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_20%,rgba(183,148,246,0.22),rgba(8,7,12,0)_48%),radial-gradient(circle_at_50%_85%,rgba(246,182,213,0.18),rgba(8,7,12,0)_42%)]" />

      <AnimatePresence mode="wait">
        {!isSubmitted ? (
          <motion.section
            key="form-stage"
            initial={{ opacity: 0, y: 24, scale: 0.98, filter: "blur(8px)" }}
            animate={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: -10, scale: 0.95, filter: "blur(12px)" }}
            transition={{ duration: 0.72, ease: easeOutExpo }}
            className="relative z-10 w-full max-w-xl rounded-3xl border border-white/10 bg-white/[0.06] p-7 shadow-[0_20px_80px_rgba(185,123,255,0.2)] backdrop-blur-xl sm:p-9"
          >
            <p className="text-xs uppercase tracking-[0.2em] text-white/60">AsterNova Voice Setup</p>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">Choose your experience</h1>

            <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
              {["Narration", "Conversation", "Game NPC", "Podcast"].map((item) => (
                <button
                  key={item}
                  type="button"
                  className="rounded-2xl border border-white/15 bg-white/[0.03] px-4 py-3 text-left text-sm font-medium text-white/90 transition duration-300 hover:border-violet-300/60 hover:bg-violet-300/10 hover:text-white"
                >
                  {item}
                </button>
              ))}
            </div>

            <button
              type="button"
              onClick={() => setIsSubmitted(true)}
              className="mt-7 inline-flex w-full items-center justify-center rounded-2xl bg-gradient-to-r from-pink-300 via-fuchsia-300 to-violet-400 px-5 py-3 text-sm font-semibold text-black shadow-[0_8px_30px_rgba(214,126,255,0.42)] transition duration-300 hover:scale-[1.01] hover:shadow-[0_16px_48px_rgba(214,126,255,0.52)]"
            >
              Continue
            </button>
          </motion.section>
        ) : (
          <motion.section
            key="loading-stage"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            transition={{ duration: 0.7, ease: easeOutExpo }}
            className="relative z-10 flex flex-col items-center justify-center"
          >
            <FluidBlob />

            <motion.div
              initial={{ opacity: 0, y: 8, scale: 0.92 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ delay: 0.3, duration: 0.75, ease: easeOutExpo }}
              className="pointer-events-none absolute inset-0 flex items-center justify-center"
            >
              <span className="bg-gradient-to-r from-pink-100 via-purple-100 to-violet-200 bg-clip-text text-3xl font-semibold tracking-[0.08em] text-transparent drop-shadow-[0_0_24px_rgba(237,190,255,0.58)] sm:text-5xl">
                AsterNova
              </span>
            </motion.div>
          </motion.section>
        )}
      </AnimatePresence>
    </main>
  )
}
