"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { AnimatePresence, LayoutGroup, motion } from "framer-motion"
import {
  ChevronRight,
  Cpu,
  Footprints,
  Gamepad2,
  HeartPulse,
  IdCard,
  Layers,
  Loader2,
  MoonStar,
  Orbit,
  Shield,
  Sparkles,
  Swords,
  Target,
  Zap,
} from "lucide-react"
import { toast } from "sonner"

import { LobbyAvatarPickerModal, LobbyPresetAvatar, useLobbyAvatar } from "@/src/components/lobby/LobbyAvatars"
import { LoopingBgmControl } from "@/src/components/audio/LoopingBgmControl"
import { wsUrl } from "@/src/config/public-env"
import { useGameStore } from "@/src/store/useGameStore"
import { useGameStoreRehydrated } from "@/src/store/useGameStoreHydration"

const uiFont = 'system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Segoe UI", sans-serif'

const easeOut = [0.22, 1, 0.36, 1] as const

const pageVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06, delayChildren: 0.04 },
  },
}

const sectionVariants = {
  hidden: { opacity: 0, y: 18 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: easeOut },
  },
}

const arcadeTileVariants = {
  hidden: { opacity: 0, y: 20 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: 0.05 * i, duration: 0.45, ease: easeOut },
  }),
}

const highlightVariants = {
  hidden: { opacity: 0, x: -8 },
  show: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: { delay: 0.06 + i * 0.05, duration: 0.35, ease: easeOut },
  }),
}

type RoleOption = {
  id: string
  name: string
  tagline: string
  highlights: string[]
  Icon: React.ComponentType<{ className?: string }>
}

const ROLES: RoleOption[] = [
  {
    id: "Role1_Speedster",
    name: "极速者",
    tagline: "光速突进，先手压制",
    highlights: ["高机动", "强突袭", "灵活走位"],
    Icon: Zap,
  },
  {
    id: "Role2_Cursemancer",
    name: "诅咒师",
    tagline: "侵蚀心智，持续消耗",
    highlights: ["减益叠加", "控场", "反制爆发"],
    Icon: MoonStar,
  },
  {
    id: "Role3_Reviver",
    name: "复苏者",
    tagline: "逆转战局，守护同伴",
    highlights: ["治疗增益", "续航", "节奏掌控"],
    Icon: HeartPulse,
  },
  {
    id: "Role4_Bulwark",
    name: "重装卫士",
    tagline: "坚壁不摧，正面推进",
    highlights: ["高防御", "嘲讽牵制", "阵地战"],
    Icon: Shield,
  },
]

type ArcadeTile = {
  href: string
  category: string
  title: string
  blurb: string
  Icon: React.ComponentType<{ className?: string }>
  accent: string
}

const ARCADE: ArcadeTile[] = [
  {
    href: "/shoot-them-all",
    category: "Physics",
    title: "Shoot Them All",
    blurb: "物理弹射 · 连锁清场",
    Icon: Target,
    accent: "from-rose-400/25 to-orange-400/10",
  },
  {
    href: "/lets-running",
    category: "Runner",
    title: "Let's Running",
    blurb: "Star Dash · 跑酷与滑铲",
    Icon: Footprints,
    accent: "from-violet-400/25 to-fuchsia-400/10",
  },
  {
    href: "/merge",
    category: "Merge",
    title: "AsterNova Merge",
    blurb: "合成星球 · 十级进化",
    Icon: Layers,
    accent: "from-fuchsia-400/22 to-purple-500/10",
  },
  {
    href: "/nebula-survivor",
    category: "Survivor",
    title: "Nebula Survivor",
    blurb: "俯视角肉鸽 · 三选一构筑",
    Icon: Orbit,
    accent: "from-sky-400/22 to-indigo-500/12",
  },
]

function GlassPanel({
  children,
  className = "",
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.5, ease: easeOut }}
      className={`rounded-[1.35rem] border border-white/[0.08] bg-white/[0.04] shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] backdrop-blur-2xl ${className}`}
      style={{ WebkitBackdropFilter: "blur(40px) saturate(180%)" }}
    >
      {children}
    </motion.div>
  )
}

function SectionRule() {
  return (
    <div className="relative my-2 h-px w-full overflow-hidden rounded-full bg-gradient-to-r from-transparent via-white/[0.12] to-transparent" />
  )
}

export default function LobbyPage() {
  const router = useRouter()

  const username = useGameStore((s) => s.username)
  const token = useGameStore((s) => s.token)
  const userId = useGameStore((s) => s.userId)

  const selectedClass = useGameStore((s) => s.selectedClass)
  const setSelectedClass = useGameStore((s) => s.setSelectedClass)

  const setCurrentRoomId = useGameStore((s) => s.setCurrentRoomId)

  const wsRef = React.useRef<WebSocket | null>(null)
  const matchingTimeoutRef = React.useRef<number | null>(null)
  const [matching, setMatching] = React.useState(false)
  const roleItemRefs = React.useRef<Record<string, HTMLButtonElement | null>>({})
  const selectedRole = React.useMemo(() => ROLES.find((r) => r.id === selectedClass) || ROLES[0], [selectedClass])

  const { avatarId, setAvatarId, pickerOpen, setPickerOpen } = useLobbyAvatar()

  const storeRehydrated = useGameStoreRehydrated()

  React.useEffect(() => {
    if (!storeRehydrated) return
    if (!token || !userId) {
      toast.error("请先登录")
      router.replace("/login")
    }
  }, [storeRehydrated, token, userId, router])

  React.useEffect(() => {
    return () => {
      if (matchingTimeoutRef.current) {
        window.clearTimeout(matchingTimeoutRef.current)
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }
      wsRef.current = null
    }
  }, [])

  function connectAndMatch() {
    if (matching) return
    if (!token) {
      toast.error("缺少 token，请先登录")
      router.push("/login")
      return
    }
    if (!userId) {
      toast.error("缺少 userId，请重新登录")
      router.push("/login")
      return
    }

    setMatching(true)

    const ws = new WebSocket(`${wsUrl}?token=${encodeURIComponent(token)}&scope=lobby`)
    wsRef.current = ws

    ws.onopen = () => {
      try {
        ws.send(JSON.stringify({ type: "match_req", user_id: userId }))
      } catch {
        toast.error("发起匹配失败：消息发送异常")
        setMatching(false)
        ws.close()
      }
    }

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(String(ev.data ?? "")) as { type?: string; room_id?: string }
        if (msg?.type === "match_success" && typeof msg.room_id === "string" && msg.room_id) {
          setCurrentRoomId(msg.room_id)
          toast.success("匹配成功！正在建立战场链接…")
          useGameStore.getState().setSessionReadyForBattle(true)
          matchingTimeoutRef.current = window.setTimeout(() => {
            router.push("/arena")
          }, 1500)
        }
      } catch {
        /* ignore */
      }
    }

    ws.onerror = () => {
      toast.error("匹配连接失败，请稍后重试")
      setMatching(false)
      try {
        ws.close()
      } catch {
        /* ignore */
      }
    }

    ws.onclose = (ev) => {
      console.debug("[LobbyWS] closed", {
        code: ev.code,
        reason: ev.reason,
        wasClean: ev.wasClean,
      })
      wsRef.current = null
      setMatching(false)
    }
  }

  const RoleIcon = selectedRole.Icon

  return (
    <div
      className="relative min-h-[100dvh] overflow-x-hidden bg-[#030303] text-white selection:bg-white/15"
      style={{ fontFamily: uiFont }}
    >
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_85%_55%_at_50%_-18%,rgba(120,119,198,0.14),transparent)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_100%_0%,rgba(59,130,246,0.055),transparent_52%)]" />
      </div>

      <motion.header
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: easeOut }}
        className="sticky top-0 z-40 border-b border-white/[0.06] bg-[#030303]/78 backdrop-blur-xl supports-[backdrop-filter]:bg-[#030303]/52"
      >
        <div className="mx-auto flex h-[3.25rem] max-w-6xl items-center justify-between gap-3 px-4 sm:px-6">
          <motion.button
            type="button"
            onClick={() => router.push("/")}
            className="group relative flex items-center gap-3 rounded-2xl px-1.5 py-1 text-left transition"
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            transition={{ type: "spring", stiffness: 520, damping: 28 }}
            aria-label="返回主页面"
            title="返回主页面"
          >
            <motion.div
              className="relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-2xl border border-white/20 bg-white/[0.14] ring-1 ring-white/[0.28] shadow-[0_0_20px_rgba(255,255,255,0.16),inset_0_1px_0_rgba(255,255,255,0.45)]"
              whileHover={{ rotate: [0, -6, 6, 0] }}
              transition={{ duration: 0.5 }}
            >
              <span className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_30%_18%,rgba(255,255,255,0.48),transparent_60%)]" />
              <Sparkles className="relative z-[1] h-[1.15rem] w-[1.15rem] text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.48)]" strokeWidth={1.7} />
            </motion.div>
            <div className="leading-[1.15]">
              <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-white/40 transition-colors group-hover:text-white/65">AsterNova</p>
              <p className="mt-0.5 text-[15px] font-semibold tracking-[-0.02em] text-white/96">大厅</p>
            </div>
          </motion.button>
          <motion.div
            className="flex items-center gap-2.5 rounded-full border border-white/[0.1] bg-white/[0.05] py-1.5 pl-1.5 pr-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] sm:pr-4"
            whileHover={{ borderColor: "rgba(255,255,255,0.16)", backgroundColor: "rgba(255,255,255,0.07)" }}
            transition={{ type: "spring", stiffness: 420, damping: 26 }}
          >
            <motion.button
              type="button"
              title="更换头像"
              aria-label="打开头像选择"
              onClick={() => setPickerOpen(true)}
              whileHover={{ scale: 1.06 }}
              whileTap={{ scale: 0.92 }}
              className="relative flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-full bg-white/[0.12] ring-2 ring-white/25 ring-offset-2 ring-offset-[#030303] transition hover:ring-white/45"
            >
              <LobbyPresetAvatar id={avatarId} className="h-8 w-8" />
            </motion.button>
            <span className="max-w-[10rem] truncate text-[13px] font-medium tracking-[-0.01em] text-white/88 sm:max-w-[14rem]">
              {username || "访客"}
            </span>
          </motion.div>
        </div>
      </motion.header>

      <motion.main
        variants={pageVariants}
        initial="hidden"
        animate="show"
        className="relative z-10 mx-auto max-w-6xl space-y-12 px-4 py-9 pb-40 sm:space-y-14 sm:px-6 sm:py-11 sm:pb-36 md:space-y-[3.25rem] md:pb-32"
      >
        <motion.section variants={sectionVariants} className="space-y-6">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
            <div className="flex gap-4">
              <motion.div
                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-[0.95rem] bg-white/[0.07] ring-1 ring-white/[0.09]"
                whileHover={{ scale: 1.05, rotate: -2 }}
                transition={{ type: "spring", stiffness: 400, damping: 22 }}
              >
                <Gamepad2 className="h-[1.35rem] w-[1.35rem] text-white/82" strokeWidth={1.6} />
              </motion.div>
              <div className="min-w-0 pt-0.5">
                <p className="text-[10px] font-semibold uppercase tracking-[0.26em] text-white/34">Offline</p>
                <h2 className="mt-1.5 text-[1.65rem] font-semibold leading-[1.15] tracking-[-0.03em] text-white sm:text-[1.85rem]">
                  休闲小游戏
                </h2>
                <p className="mt-2 max-w-[26rem] text-[14px] leading-[1.55] text-white/44">
                  无需匹配，本地即玩。与下方联机战场互不干扰。
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 sm:gap-4 lg:grid-cols-4">
            {ARCADE.map((game, i) => (
              <motion.button
                key={game.href}
                type="button"
                custom={i}
                variants={arcadeTileVariants}
                initial="hidden"
                animate="show"
                whileHover={{ y: -5, transition: { type: "spring", stiffness: 420, damping: 22 } }}
                whileTap={{ scale: 0.97, y: -1 }}
                onClick={() => router.push(game.href)}
                className="group relative flex flex-col overflow-hidden rounded-[1.28rem] border border-white/[0.07] bg-white/[0.035] p-[1.05rem] pb-[1.15rem] text-left shadow-[inset_0_1px_0_rgba(255,255,255,0.05),0_2px_24px_rgba(0,0,0,0.25)] transition-[border-color,box-shadow] duration-300 hover:border-white/[0.14] hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.07),0_12px_40px_rgba(0,0,0,0.35)]"
                style={{ WebkitBackdropFilter: "blur(26px)" }}
              >
                <div
                  className={`pointer-events-none absolute -right-10 -top-10 h-32 w-32 rounded-full bg-gradient-to-br opacity-[0.55] blur-3xl transition-opacity duration-500 group-hover:opacity-[0.75] ${game.accent}`}
                />
                <div className="relative flex items-start justify-between gap-3">
                  <motion.div
                    className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/[0.1] ring-1 ring-white/[0.08]"
                    whileHover={{ scale: 1.08 }}
                    transition={{ type: "spring", stiffness: 500, damping: 20 }}
                  >
                    <game.Icon
                      className="h-[1.2rem] w-[1.2rem] text-white/92 transition-transform duration-300 group-hover:scale-105"
                      strokeWidth={1.7}
                    />
                  </motion.div>
                  <span className="rounded-full border border-white/[0.08] bg-black/25 px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.14em] text-white/38">
                    {game.category}
                  </span>
                </div>
                <p className="relative mt-4 text-[15px] font-semibold leading-snug tracking-[-0.02em] text-white">{game.title}</p>
                <p className="relative mt-1.5 text-[13px] leading-[1.45] text-white/46">{game.blurb}</p>
                <div className="relative mt-auto pt-5">
                  <span className="lobby-arcade-enter-pill relative inline-flex items-center gap-1.5 rounded-full border border-white/40 bg-white/[0.2] px-4 py-2.5 text-[13px] font-semibold text-white tabular-nums">
                    <span
                      className="pointer-events-none absolute inset-0 overflow-hidden rounded-full"
                      aria-hidden
                    >
                      <span className="lobby-arcade-sheen pointer-events-none absolute left-0 top-0 h-full w-[55%] bg-gradient-to-r from-transparent via-white/40 to-transparent" />
                    </span>
                    <span className="relative drop-shadow-[0_0_8px_rgba(255,255,255,0.35)]">进入</span>
                    <ChevronRight
                      className="relative h-4 w-4 text-white transition-transform duration-300 group-hover:translate-x-1"
                      strokeWidth={2.5}
                    />
                  </span>
                </div>
              </motion.button>
            ))}
          </div>
        </motion.section>

        <motion.div variants={sectionVariants}>
          <SectionRule />
        </motion.div>

        <motion.section variants={sectionVariants} className="space-y-6">
          <div className="flex gap-4">
            <motion.div
              className="flex h-12 w-12 shrink-0 items-center justify-center rounded-[0.95rem] bg-white/[0.07] ring-1 ring-white/[0.09]"
              whileHover={{ scale: 1.05, rotate: 2 }}
              transition={{ type: "spring", stiffness: 400, damping: 22 }}
            >
              <Swords className="h-[1.35rem] w-[1.35rem] text-white/76" strokeWidth={1.6} />
            </motion.div>
            <div className="min-w-0 pt-0.5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.26em] text-white/34">Online</p>
              <h2 className="mt-1.5 text-[1.65rem] font-semibold leading-[1.15] tracking-[-0.03em] text-white sm:text-[1.85rem]">
                联机战场
              </h2>
              <p className="mt-2 max-w-[26rem] text-[14px] leading-[1.55] text-white/44">
                选择职业后匹配进入竞技场。右侧列表可滚动切换。
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1.12fr_0.88fr] lg:gap-7">
            <GlassPanel className="overflow-hidden p-5 sm:p-7">
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-white/[0.06] pb-6">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={selectedRole.id}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 10 }}
                    transition={{ duration: 0.3, ease: easeOut }}
                    className="flex items-center gap-4"
                  >
                    <motion.div
                      layout
                      className="flex h-[3.6rem] w-[3.6rem] items-center justify-center rounded-[1.05rem] bg-gradient-to-br from-white/[0.14] to-white/[0.04] ring-1 ring-white/[0.1]"
                    >
                      <RoleIcon className="h-7 w-7 text-white/88" strokeWidth={1.45} />
                    </motion.div>
                    <div>
                      <p className="text-[12px] font-medium text-white/38">当前职业</p>
                      <p className="mt-1 text-[1.35rem] font-semibold leading-tight tracking-[-0.03em]">{selectedRole.name}</p>
                      <p className="mt-1.5 text-[14px] leading-snug text-white/48">{selectedRole.tagline}</p>
                    </div>
                  </motion.div>
                </AnimatePresence>
              </div>

              <div className="mt-6 space-y-2.5">
                <motion.div
                  whileHover={{ borderColor: "rgba(255,255,255,0.1)", backgroundColor: "rgba(0,0,0,0.32)" }}
                  className="flex items-center gap-3 rounded-xl border border-white/[0.06] bg-black/[0.22] px-3.5 py-3 transition-colors duration-200"
                >
                  <IdCard className="h-4 w-4 shrink-0 text-white/32" strokeWidth={1.75} />
                  <div className="min-w-0 flex-1">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-white/32">User ID</p>
                    <p className="mt-0.5 truncate font-mono text-[12px] text-white/74">{userId || "—"}</p>
                  </div>
                </motion.div>
                <motion.div
                  whileHover={{ borderColor: "rgba(255,255,255,0.1)", backgroundColor: "rgba(0,0,0,0.32)" }}
                  className="flex items-center gap-3 rounded-xl border border-white/[0.06] bg-black/[0.22] px-3.5 py-3 transition-colors duration-200"
                >
                  <Cpu className="h-4 w-4 shrink-0 text-white/32" strokeWidth={1.75} />
                  <div className="min-w-0 flex-1">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-white/32">Role key</p>
                    <p className="mt-0.5 truncate font-mono text-[11px] text-white/62">{selectedRole.id}</p>
                  </div>
                </motion.div>
              </div>

              <ul className="mt-6 space-y-2">
                {selectedRole.highlights.map((h, i) => (
                  <motion.li
                    key={`${selectedRole.id}-${h}`}
                    custom={i}
                    variants={highlightVariants}
                    initial="hidden"
                    animate="show"
                    className="flex items-center gap-3 text-[14px] leading-snug text-white/70"
                  >
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white/[0.07] ring-1 ring-white/[0.06]">
                      <span className="h-1 w-1 rounded-full bg-white/55" />
                    </span>
                    {h}
                  </motion.li>
                ))}
              </ul>

              <motion.div
                className="mt-8 overflow-hidden rounded-2xl border border-dashed border-white/[0.1] bg-black/[0.28]"
                initial={false}
                animate={{ borderColor: "rgba(255,255,255,0.1)" }}
              >
                <div className="flex aspect-[16/10] max-h-[280px] flex-col items-center justify-center gap-2 px-6 py-10 sm:max-h-[300px]">
                  <motion.div
                    animate={{ y: [0, -4, 0] }}
                    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                    className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-3.5"
                  >
                    <RoleIcon className="h-8 w-8 text-white/28" strokeWidth={1.2} />
                  </motion.div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.3em] text-white/28">Preview</p>
                  <p className="max-w-[16rem] text-center text-[13px] leading-relaxed text-white/38">
                    角色展示位 · 待接入模型 / 立绘
                  </p>
                </div>
              </motion.div>
            </GlassPanel>

            <GlassPanel className="flex flex-col overflow-hidden">
              <div className="border-b border-white/[0.06] px-5 py-4 sm:px-7 sm:py-5">
                <p className="text-[15px] font-semibold tracking-[-0.02em]">职业</p>
                <p className="mt-1 text-[13px] text-white/40">轻点切换 · 弹簧反馈</p>
              </div>
              <LayoutGroup id="roles">
                <div className="max-h-[min(58vh,520px)] space-y-1 overflow-y-auto p-2.5 sm:p-3.5 [scrollbar-width:thin]">
                  {ROLES.map((role) => {
                    const active = selectedClass === role.id
                    const RIcon = role.Icon
                    return (
                      <motion.button
                        key={role.id}
                        type="button"
                        layout
                        ref={(el) => {
                          roleItemRefs.current[role.id] = el
                        }}
                        onClick={() => {
                          setSelectedClass(role.id)
                          const el = roleItemRefs.current[role.id]
                          if (el) {
                            try {
                              el.scrollIntoView({ block: "center", behavior: "smooth" })
                            } catch {
                              /* ignore */
                            }
                          }
                        }}
                        whileHover={{ backgroundColor: "rgba(255,255,255,0.06)" }}
                        whileTap={{ scale: 0.985 }}
                        transition={{ type: "spring", stiffness: 520, damping: 32 }}
                        className="relative flex w-full items-center gap-3 overflow-hidden rounded-xl px-3 py-3 text-left"
                      >
                        {active ? (
                          <motion.div
                            layoutId="roleActiveBg"
                            className="absolute inset-0 rounded-xl bg-white/[0.1] ring-1 ring-white/[0.14]"
                            transition={{ type: "spring", stiffness: 380, damping: 32 }}
                          />
                        ) : null}
                        <motion.div
                          layout
                          className={[
                            "relative z-[1] flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl ring-1",
                            active ? "bg-white/[0.16] ring-white/22" : "bg-white/[0.06] ring-white/[0.06]",
                          ].join(" ")}
                          animate={active ? { scale: [1, 1.06, 1] } : { scale: 1 }}
                          transition={{ duration: 0.35 }}
                        >
                          <RIcon className="h-[1.15rem] w-[1.15rem] text-white/88" strokeWidth={1.75} />
                        </motion.div>
                        <div className="relative z-[1] min-w-0 flex-1">
                          <p className="text-[15px] font-medium leading-tight tracking-[-0.02em]">{role.name}</p>
                          <p className="mt-0.5 truncate text-[12px] text-white/42">{role.tagline}</p>
                        </div>
                        <span className="relative z-[1] shrink-0">
                          {active ? (
                            <span className="inline-block rounded-full bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-black">
                              已选
                            </span>
                          ) : (
                            <ChevronRight className="h-4 w-4 text-white/22" strokeWidth={2} />
                          )}
                        </span>
                      </motion.button>
                    )
                  })}
                </div>
              </LayoutGroup>
            </GlassPanel>
          </div>
        </motion.section>
      </motion.main>

      <div className="pointer-events-none fixed inset-x-0 bottom-0 z-50 flex justify-center bg-gradient-to-t from-[#030303] via-[#030303]/92 to-transparent pb-[max(1.1rem,env(safe-area-inset-bottom))] pt-16">
        <motion.button
          type="button"
          disabled={matching}
          onClick={connectAndMatch}
          whileHover={
            matching
              ? undefined
              : {
                  scale: 1.03,
                  boxShadow: "0 16px 48px rgba(255,255,255,0.14), 0 0 0 1px rgba(255,255,255,0.2) inset",
                }
          }
          whileTap={matching ? undefined : { scale: 0.96 }}
          transition={{ type: "spring", stiffness: 460, damping: 26 }}
          className="pointer-events-auto group relative flex min-h-[54px] w-full max-w-[min(100%-2rem,28rem)] items-center justify-center gap-2.5 overflow-hidden rounded-full bg-white px-8 text-[15px] font-semibold tracking-[-0.02em] text-black shadow-[0_10px_40px_rgba(0,0,0,0.5),0_0_0_1px_rgba(255,255,255,0.14)_inset] transition-shadow disabled:cursor-not-allowed disabled:opacity-[0.52]"
        >
          {!matching ? (
            <span
              className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
              style={{
                background:
                  "linear-gradient(105deg, transparent 38%, rgba(255,255,255,0.5) 50%, transparent 62%)",
              }}
            />
          ) : null}
          {matching ? (
            <span className="relative flex items-center gap-2.5">
              <Loader2 className="h-5 w-5 animate-spin text-black/78" strokeWidth={2} />
              <span>匹配中…</span>
            </span>
          ) : (
            <span className="relative flex items-center gap-2.5">
              <Swords className="h-[1.12rem] w-[1.12rem] text-black/88" strokeWidth={2} />
              <span>开始匹配</span>
            </span>
          )}
        </motion.button>
      </div>

      <LobbyAvatarPickerModal
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        currentId={avatarId}
        onSelect={setAvatarId}
      />
      <LoopingBgmControl src="/audio/lobby/my_track  startgame.mp3" storageKey="bgm-volume:lobby" />
    </div>
  )
}
