"use client"

import * as React from "react"
import Image from "next/image"
import { useRouter } from "next/navigation"
import { AnimatePresence, motion, useReducedMotion } from "framer-motion"
import { toast } from "sonner"
import dynamic from "next/dynamic"

import { cinematicEase } from "@/src/lib/motion"
import { KEY_ART, type KeyArtSlug } from "@/src/lib/keyArt"
import {
  LobbyAvatarPickerModal,
  LobbyPresetAvatar,
  useLobbyAvatar,
} from "@/src/components/lobby/LobbyAvatars"
import { LoopingBgmControl } from "@/src/components/audio/LoopingBgmControl"
import * as Hud from "@/src/components/icons/arcade-icons"
import { wsUrl } from "@/src/config/public-env"
import { useGameStore } from "@/src/store/useGameStore"
import { useGameStoreRehydrated } from "@/src/store/useGameStoreHydration"

const CinematicBlackHole = dynamic(
  () => import("@/src/components/CinematicBlackHole").then((m) => m.CinematicBlackHole),
  { ssr: false, loading: () => <div className="absolute inset-0 bg-ink-900" /> },
)

const easeOut = cinematicEase
const CJK = /[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]/
const hasCJK = (s: string) => CJK.test(s)

/* ============================ 数据 ============================ */

type ArcadeTile = {
  slug: KeyArtSlug
  href: string
  index: string
  category: string
  title: string
  blurb: string
  Icon: React.ComponentType<Hud.HudIconProps>
  featured?: boolean
}

const ARCADE: ArcadeTile[] = [
  {
    slug: "nebula-survivor",
    href: "/nebula-survivor",
    index: "01",
    category: "Survivor",
    title: "Nebula Survivor",
    blurb: "俯视角肉鸽 · 三选一构筑 · 五条强化轨道",
    Icon: Hud.HudRadar,
    featured: true,
  },
  {
    slug: "shoot-them-all",
    href: "/shoot-them-all",
    index: "02",
    category: "Physics",
    title: "Shoot Them All",
    blurb: "物理弹射 · 连锁清场",
    Icon: Hud.HudTarget,
  },
  {
    slug: "lets-running",
    href: "/lets-running",
    index: "03",
    category: "Runner",
    title: "Let's Running",
    blurb: "跑酷滑铲 · 极限冲刺",
    Icon: Hud.HudRunner,
  },
  {
    slug: "merge",
    href: "/merge",
    index: "04",
    category: "Merge",
    title: "AsterNova Merge",
    blurb: "合成星球 · 十级进化",
    Icon: Hud.HudMerge,
  },
  {
    slug: "xiaoxiaole",
    href: "/xiaoxiaole",
    index: "05",
    category: "Match-3",
    title: "恒睿消消乐",
    blurb: "立体三消 · 12 关闯关",
    Icon: Hud.HudHexGem,
  },
]

const ARCADE_ART = "/art/arcade"

type RoleOption = {
  id: string
  name: string
  tagline: string
  highlights: string[]
  /**
   * 铭牌上的三条倾向刻度（0~1）。
   * ⚠️ 纯展示占位：角色数值平衡属 M2 范畴，尚未定案。
   *    接入真实配置表前，请勿把这里的数值当作玩法数据引用。
   */
  traits: [number, number, number]
  Icon: React.ComponentType<Hud.HudIconProps>
}

const TRAIT_LABELS = ["机动", "控制", "续航"] as const

const ROLES: RoleOption[] = [
  {
    id: "Role1_Speedster",
    name: "极速者",
    tagline: "光速突进，先手压制",
    highlights: ["高机动", "强突袭", "灵活走位"],
    traits: [0.95, 0.45, 0.4],
    Icon: Hud.HudBolt,
  },
  {
    id: "Role2_Cursemancer",
    name: "诅咒师",
    tagline: "侵蚀心智，持续消耗",
    highlights: ["减益叠加", "控场", "反制爆发"],
    traits: [0.45, 0.9, 0.5],
    Icon: Hud.HudMoonStar,
  },
  {
    id: "Role3_Reviver",
    name: "复苏者",
    tagline: "逆转战局，守护同伴",
    highlights: ["治疗增益", "续航", "节奏掌控"],
    traits: [0.4, 0.55, 0.95],
    Icon: Hud.HudRevive,
  },
  {
    id: "Role4_Bulwark",
    name: "重装卫士",
    tagline: "坚壁不摧，正面推进",
    highlights: ["高防御", "嘲讽牵制", "阵地战"],
    traits: [0.25, 0.7, 0.85],
    Icon: Hud.HudShield,
  },
]

/* ============================ 局部组件 ============================ */

/** 分段主标题：序号 + 大字号 + 刻度收边 */
function SectionHeading({
  index,
  tag,
  title,
  desc,
  Icon,
}: {
  index: string
  tag: string
  title: string
  desc: string
  Icon: React.ComponentType<Hud.HudIconProps>
}) {
  return (
    <div className="flex items-start gap-4">
      <span className="relative mt-1 flex h-12 w-12 shrink-0 items-center justify-center border border-hud-line bg-hud-raised text-hud-accent">
        <Icon className="h-[1.4rem] w-[1.4rem]" strokeWidth={1.5} />
        <span className="absolute -left-px -top-px h-2 w-2 border-l border-t border-hud-accent" />
        <span className="absolute -bottom-px -right-px h-2 w-2 border-b border-r border-hud-accent" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="flex items-center gap-2.5 font-mono-data text-[11px] uppercase tracking-[0.26em]">
          <span className="text-hud-accent">{index}</span>
          <span className="h-px w-5 bg-hud-line-strong" />
          <span className="text-hud-text-dim">{tag}</span>
        </p>
        <h2 className="mt-1.5 text-[1.75rem] font-semibold leading-[1.1] tracking-[-0.035em] text-hud-paper sm:text-[2rem]">
          {title}
        </h2>
        <p className="mt-2 max-w-[38rem] text-[13.5px] leading-relaxed text-hud-text-dim">{desc}</p>
      </div>
    </div>
  )
}

/** key art 卡：美术占满整卡，文字遮罩叠加，行动召唤常亮 */
function ArcadeCard({
  tile,
  loading,
  disabled,
  onOpen,
  reduce,
}: {
  tile: ArcadeTile
  loading: boolean
  disabled: boolean
  onOpen: () => void
  reduce: boolean
}) {
  const { Icon, featured } = tile
  const art = KEY_ART[tile.slug]
  const cjk = hasCJK(tile.title)

  return (
    <motion.button
      type="button"
      onClick={onOpen}
      disabled={disabled}
      whileHover={reduce || disabled ? undefined : { y: -3 }}
      whileTap={reduce || disabled ? undefined : { y: -1, scale: 0.995 }}
      transition={{ duration: 0.22, ease: easeOut }}
      className={[
        "group relative block w-full overflow-hidden border border-hud-line bg-ink-800 text-left",
        "aspect-[3/2] transition-[border-color,box-shadow] duration-200 lg:aspect-auto lg:h-full",
        "hud-chamfer hud-corners",
        "hover:border-hud-accent/55 hover:shadow-[var(--glow-accent)]",
        "focus-visible:outline-none focus-visible:border-hud-accent",
        "disabled:cursor-progress",
        featured ? "sm:col-span-2 lg:col-span-6 lg:row-span-2" : "lg:col-span-3",
      ].join(" ")}
      aria-label={`进入 ${tile.title}`}
    >
      {/* key art（next/image：自动 AVIF/WebP + srcset + LQIP 模糊占位，消除加载白闪） */}
      <Image
        src={`${ARCADE_ART}/${tile.slug}.webp`}
        alt=""
        fill
        priority={featured}
        placeholder="blur"
        blurDataURL={art.lqip}
        sizes={
          featured
            ? "(min-width: 1024px) 620px, (min-width: 640px) 100vw, 100vw"
            : "(min-width: 1024px) 300px, (min-width: 640px) 50vw, 100vw"
        }
        className="object-cover transition-transform duration-[600ms] ease-out group-hover:scale-[1.05]"
      />

      {/* 可读性遮罩（单色 scrim，非装饰渐变） */}
      <div className="absolute inset-0 bg-gradient-to-t from-ink-1000 via-ink-1000/55 to-transparent" />
      <div className="absolute inset-0 bg-gradient-to-r from-ink-1000/45 to-transparent" />

      {/* 悬停扫描光带 */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="hud-sweep absolute inset-y-0 left-0 w-1/4 bg-white/[0.07]" />
      </div>

      {/* 内容 */}
      <div className="relative flex h-full flex-col justify-between p-4 sm:p-5">
        <div className="flex items-start justify-between gap-3">
          <span className="flex items-center gap-2 font-mono-data text-[11px] tracking-[0.2em] text-hud-text-dim">
            <Icon className="h-4 w-4 text-hud-accent" strokeWidth={1.6} />
            {tile.index}
          </span>
          <span className="flex items-center gap-2">
            {featured ? (
              <span className="flex items-center gap-1.5 border border-hud-accent/55 bg-hud-accent/15 px-2 py-0.5 font-mono-data text-[9.5px] uppercase tracking-[0.18em] text-hud-accent-bright backdrop-blur-sm">
                <span className="h-1 w-1 animate-pulse bg-hud-accent" />
                精选
              </span>
            ) : null}
            <span className="border border-hud-line bg-ink-1000/55 px-2 py-0.5 font-mono-data text-[9.5px] uppercase tracking-[0.16em] text-hud-text-dim backdrop-blur-sm">
              {tile.category}
            </span>
          </span>
        </div>

        <div>
          <h3
            className={[
              "font-bold leading-[1.05] text-hud-paper",
              cjk
                ? "font-sans tracking-[-0.03em]"
                : "font-display tracking-[-0.01em]",
              featured ? "text-[1.35rem] sm:text-[1.9rem]" : "text-[1.05rem] sm:text-[1.15rem]",
            ].join(" ")}
          >
            {tile.title}
          </h3>
          <p
            className={[
              "mt-1.5 leading-snug text-hud-text",
              featured ? "max-w-[34rem] text-[13px] sm:text-[14px]" : "hidden text-[12px] sm:block",
            ].join(" ")}
          >
            {tile.blurb}
          </p>

          {/* 常亮行动召唤 */}
          <span className="mt-3.5 inline-flex items-center gap-1.5 border border-hud-accent/55 bg-hud-accent/15 px-3 py-1.5 text-[12.5px] font-medium text-hud-accent-bright backdrop-blur-sm transition-colors duration-150 group-hover:border-hud-accent group-hover:bg-hud-accent group-hover:text-ink-1000">
            {loading ? "载入中" : "进入"}
            <Hud.HudChevronRight className="h-3.5 w-3.5" strokeWidth={2} />
          </span>
        </div>
      </div>

      {loading ? (
        <span className="absolute inset-x-0 bottom-0 h-[3px] overflow-hidden bg-ink-1000/70">
          <span className="hud-progress block h-full w-full bg-hud-accent" />
        </span>
      ) : null}
    </motion.button>
  )
}

/** 账号详情：可控展开 + 高度动效（保留 aria 语义） */
function AccountDetails({ userId, roleId }: { userId: string | number; roleId: string }) {
  const [open, setOpen] = React.useState(false)
  return (
    <div className="mt-3 border border-hud-line bg-ink-900/40">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls="lobby-account-details"
        className="flex w-full items-center justify-between px-3 py-2 text-[12px] text-hud-text-dim transition-colors duration-150 hover:text-hud-text focus-visible:outline-none"
      >
        账号详情
        <Hud.HudChevronRight
          className={`h-3.5 w-3.5 transition-transform duration-200 ${open ? "rotate-90" : ""}`}
          strokeWidth={1.75}
        />
      </button>
      <AnimatePresence initial={false}>
        {open ? (
          <motion.dl
            id="lobby-account-details"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.24, ease: easeOut }}
            className="overflow-hidden border-t border-hud-line"
          >
            <div className="space-y-2 px-3 py-2.5">
              <div className="flex items-center gap-2">
                <Hud.HudIdCard className="h-3.5 w-3.5 shrink-0 text-hud-text-faint" strokeWidth={1.5} />
                <dt className="text-[11px] text-hud-text-faint">User ID</dt>
                <dd className="ml-auto truncate font-mono-data text-[11.5px] text-hud-text-dim">{userId || "—"}</dd>
              </div>
              <div className="flex items-center gap-2">
                <Hud.HudChip className="h-3.5 w-3.5 shrink-0 text-hud-text-faint" strokeWidth={1.5} />
                <dt className="text-[11px] text-hud-text-faint">Role key</dt>
                <dd className="ml-auto truncate font-mono-data text-[11.5px] text-hud-text-dim">{roleId}</dd>
              </div>
            </div>
          </motion.dl>
        ) : null}
      </AnimatePresence>
    </div>
  )
}

/* ============================ 页面 ============================ */

export default function LobbyPage() {
  const router = useRouter()
  const reduce = useReducedMotion() ?? false

  const username = useGameStore((s) => s.username)
  const token = useGameStore((s) => s.token)
  const userId = useGameStore((s) => s.userId)

  const selectedClass = useGameStore((s) => s.selectedClass)
  const setSelectedClass = useGameStore((s) => s.setSelectedClass)

  const setCurrentRoomId = useGameStore((s) => s.setCurrentRoomId)

  const wsRef = React.useRef<WebSocket | null>(null)
  const matchingTimeoutRef = React.useRef<number | null>(null)
  const roleItemRefs = React.useRef<Record<string, HTMLButtonElement | null>>({})
  const [matching, setMatching] = React.useState(false)
  const [navigating, setNavigating] = React.useState<string | null>(null)

  const selectedRole = React.useMemo(
    () => ROLES.find((r) => r.id === selectedClass) || ROLES[0],
    [selectedClass],
  )

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

  /** 仅关闭既有连接并复位 UI 状态；不改协议、不改 store 契约。 */
  function cancelMatch() {
    if (matchingTimeoutRef.current) {
      window.clearTimeout(matchingTimeoutRef.current)
      matchingTimeoutRef.current = null
    }
    try {
      wsRef.current?.close()
    } catch {
      /* ignore */
    }
    wsRef.current = null
    setMatching(false)
  }

  const RoleIcon = selectedRole.Icon

  const matchButton = (variant: "panel" | "bar") => {
    const height = variant === "bar" ? "min-h-[50px]" : "min-h-[46px]"
    if (matching) {
      return (
        <div className="flex w-full items-stretch gap-2">
          <div
            className={`${height} relative flex flex-1 items-center justify-center gap-2.5 overflow-hidden border border-hud-accent/45 bg-hud-accent/12 px-4`}
          >
            <span className="absolute inset-x-0 bottom-0 h-[2px] overflow-hidden bg-ink-1000/60">
              <span className="hud-progress block h-full w-full bg-hud-accent" />
            </span>
            <Hud.HudSpinner className="h-4 w-4 animate-spin text-hud-accent" strokeWidth={1.75} />
            <span className="font-mono-data text-[13px] uppercase tracking-[0.18em] text-hud-accent">匹配中</span>
          </div>
          <button
            type="button"
            onClick={cancelMatch}
            className={`${height} flex items-center gap-1.5 border border-hud-line px-4 font-mono-data text-[12.5px] uppercase tracking-[0.14em] text-hud-text-dim transition-colors duration-150 hover:border-hud-red/50 hover:text-hud-red focus-visible:outline-none focus-visible:border-hud-accent`}
          >
            <Hud.HudClose className="h-3.5 w-3.5" strokeWidth={1.75} />
            取消
          </button>
        </div>
      )
    }
    return (
      <button
        type="button"
        onClick={connectAndMatch}
        className={`${height} group/cta relative flex w-full items-center justify-center gap-2.5 overflow-hidden border border-hud-accent/60 bg-hud-accent px-6 text-[15px] font-semibold tracking-[-0.01em] text-ink-1000 transition-colors duration-150 hover:bg-hud-accent-bright focus-visible:outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-hud-accent`}
      >
        <Hud.HudSwords className="h-[1.1rem] w-[1.1rem]" strokeWidth={1.75} />
        <span>开始匹配</span>
        <Hud.HudChevronRight className="h-4 w-4 transition-transform duration-200 group-hover/cta:translate-x-1" strokeWidth={2} />
      </button>
    )
  }

  return (
    <div className="relative min-h-[100dvh] overflow-x-hidden bg-ink-900 text-hud-text selection:bg-hud-accent selection:text-ink-900">
      {/* ===== 背景氛围层 ===== */}
      <div className="pointer-events-none fixed inset-0 z-0">
        <CinematicBlackHole interactive={false} intensity={0.55} opacity={0.30} />
        <div
          className="absolute inset-0 bg-cover bg-center opacity-20 mix-blend-screen
                     [mask-image:radial-gradient(ellipse_78%_62%_at_50%_32%,black_0%,transparent_74%)]
                     [-webkit-mask-image:radial-gradient(ellipse_78%_62%_at_50%_32%,black_0%,transparent_74%)]"
          style={{ backgroundImage: `url(${ARCADE_ART}/bg-nebula.webp)` }}
        />
        <div className="star-chart-grid absolute inset-0 opacity-25" />
        <div className="absolute inset-0 bg-[linear-gradient(to_bottom,var(--ink-900)_0%,transparent_16%,transparent_72%,var(--ink-900)_100%)]" />
      </div>

      {/* ===== 顶栏 ===== */}
      <motion.header
        initial={reduce ? false : { opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: easeOut }}
        className="sticky top-0 z-40 border-b border-hud-line bg-ink-900/80 backdrop-blur-xl"
      >
        <div className="mx-auto flex h-[3.75rem] max-w-7xl items-center justify-between gap-3 px-4 sm:px-6">
          <button
            type="button"
            onClick={() => router.push("/")}
            className="group flex items-center gap-2.5 text-left focus-visible:outline-none"
            aria-label="返回主页面"
          >
            <span className="hud-chamfer-sm flex h-8 w-8 items-center justify-center border border-hud-line bg-hud-raised text-hud-accent transition-colors duration-150 group-hover:border-hud-accent/50">
              <Hud.HudSpark className="h-4 w-4" strokeWidth={1.5} />
            </span>
            <span className="leading-none">
              <span className="font-display block text-[10px] font-bold uppercase tracking-[0.24em] text-hud-text-dim">
                AsterNova
              </span>
              <span className="mt-1 block text-[15px] font-semibold tracking-[-0.01em] text-hud-paper">大厅</span>
            </span>
          </button>

          <div className="flex items-center gap-2 sm:gap-2.5">
            {/* 音乐控件内联在顶栏：彻底消除悬浮控件压住卡片内容 */}
            <LoopingBgmControl
              src="/audio/lobby/my_track  startgame.mp3"
              storageKey="bgm-volume:lobby"
              variant="inline"
            />

            <div className="flex items-center gap-2.5 border border-hud-line bg-hud-raised py-1 pl-1 pr-3">
              <button
                type="button"
                title="更换头像"
                aria-label="打开头像选择"
                onClick={() => setPickerOpen(true)}
                className="relative flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden border border-hud-line bg-ink-900 transition-colors duration-150 hover:border-hud-accent/50 focus-visible:outline-none"
              >
                <LobbyPresetAvatar id={avatarId} className="h-7 w-7" />
              </button>
              <span className="flex min-w-0 items-center gap-1.5">
                <span className="h-1.5 w-1.5 shrink-0 animate-pulse bg-hud-green" aria-hidden />
                <span className="max-w-[7rem] truncate font-mono-data text-[12.5px] tracking-[0.02em] text-hud-text sm:max-w-[13rem]">
                  {username || "访客"}
                </span>
              </span>
            </div>
          </div>
        </div>
      </motion.header>

      {/* ===== 主体 ===== */}
      <main
        id="main-content"
        tabIndex={-1}
        className="relative z-10 mx-auto max-w-7xl px-4 py-8 pb-28 sm:px-6 sm:py-10 lg:pb-14"
      >
        <h1 className="sr-only">AsterNova 游戏大厅</h1>

        {/* ---------- 区块一 ---------- */}
        <motion.section
          initial={reduce ? false : { opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: easeOut }}
        >
          <SectionHeading
            index="01"
            tag="Arcade"
            title="休闲小游戏"
            desc="无需匹配，点击即玩。与下方联机战场互不干扰。"
            Icon={Hud.HudGamepad}
          />

          <div className="mt-6 grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-12 lg:auto-rows-[200px] lg:gap-4">
            {ARCADE.map((tile, i) => (
              <motion.div
                key={tile.href}
                initial={reduce ? false : { opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: reduce ? 0 : 0.03 * i, duration: 0.35, ease: easeOut }}
                className={tile.featured ? "sm:col-span-2 lg:col-span-6 lg:row-span-2" : "lg:col-span-3"}
              >
                <ArcadeCard
                  tile={tile}
                  reduce={reduce}
                  loading={navigating === tile.href}
                  disabled={navigating !== null}
                  onOpen={() => {
                    if (navigating) return
                    setNavigating(tile.href)
                    router.push(tile.href)
                  }}
                />
              </motion.div>
            ))}
          </div>
        </motion.section>

        {/* ---------- 区块二 ---------- */}
        <motion.section
          initial={reduce ? false : { opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: reduce ? 0 : 0.16, duration: 0.4, ease: easeOut }}
          className="mt-12 sm:mt-16"
        >
          <SectionHeading
            index="02"
            tag="Battle"
            title="联机战场"
            desc="选定职业后发起匹配，由服务端撮合进入竞技场。"
            Icon={Hud.HudSwords}
          />

          <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-[1.08fr_0.92fr]">
            {/* 左：选中职业 */}
            <section className="hud-chamfer flex flex-col border border-hud-line bg-ink-800/70 p-4 backdrop-blur-sm sm:p-5">
              <div className="flex items-center justify-between gap-3 border-b border-hud-line pb-3.5">
                <div className="flex items-center gap-3">
                  <span className="flex h-12 w-12 items-center justify-center border border-hud-accent/40 bg-hud-accent/12 text-hud-accent">
                    <RoleIcon className="h-[1.35rem] w-[1.35rem]" strokeWidth={1.5} />
                  </span>
                  <div>
                    <p className="text-[12px] text-hud-text-dim">当前职业</p>
                    <p className="mt-0.5 text-[1.25rem] font-semibold leading-none tracking-[-0.025em] text-hud-paper">
                      {selectedRole.name}
                    </p>
                  </div>
                </div>
                <p className="max-w-[45%] truncate text-right font-mono-data text-[11px] text-hud-text-faint">
                  {selectedRole.id}
                </p>
              </div>

              <p className="mt-3.5 text-[13.5px] leading-relaxed text-hud-text-dim">{selectedRole.tagline}</p>

              {/* 职业铭牌：星云底 + 准星 + 图标 + 三条倾向刻度 */}
              <div className="relative mt-4 overflow-hidden border border-hud-line bg-ink-1000/60">
                <div
                  className="absolute inset-0 bg-cover bg-center opacity-25"
                  style={{ backgroundImage: `url(${ARCADE_ART}/bg-nebula.webp)` }}
                />
                <div className="relative flex h-[132px] items-center justify-center">
                  <div className="reticle-ring absolute h-32 w-32" />
                  <RoleIcon className="relative h-11 w-11 text-hud-accent" strokeWidth={1.2} />
                </div>
                <div className="relative space-y-1.5 border-t border-hud-line bg-ink-1000/70 px-3.5 py-2.5">
                  {selectedRole.traits.map((v, i) => (
                    <div key={TRAIT_LABELS[i]} className="flex items-center gap-2.5">
                      <span className="w-8 shrink-0 text-[10.5px] text-hud-text-faint">{TRAIT_LABELS[i]}</span>
                      <span className="h-[5px] flex-1 overflow-hidden bg-ink-700">
                        <motion.span
                          className="block h-full origin-left bg-hud-accent"
                          initial={reduce ? false : { scaleX: 0 }}
                          animate={{ scaleX: v }}
                          transition={{ duration: 0.4, ease: easeOut, delay: reduce ? 0 : 0.05 * i }}
                        />
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <ul className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-3">
                <AnimatePresence mode="popLayout" initial={false}>
                  {selectedRole.highlights.map((h, i) => (
                    <motion.li
                      key={`${selectedRole.id}-${h}`}
                      initial={reduce ? false : { opacity: 0, x: -6 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={reduce ? undefined : { opacity: 0 }}
                      transition={{ delay: reduce ? 0 : 0.04 * i, duration: 0.24, ease: easeOut }}
                      className="flex items-center gap-2 border border-hud-line bg-ink-900/50 px-3 py-2 text-[13px] text-hud-text"
                    >
                      <span className="h-1.5 w-1.5 shrink-0 bg-hud-accent" />
                      {h}
                    </motion.li>
                  ))}
                </AnimatePresence>
              </ul>

              <div className="mt-5 hidden lg:block">{matchButton("panel")}</div>

              <AccountDetails userId={userId} roleId={selectedRole.id} />
            </section>

            {/* 右：职业列表 */}
            <section className="hud-chamfer flex flex-col border border-hud-line bg-ink-800/70 backdrop-blur-sm">
              <div className="border-b border-hud-line px-4 py-3.5">
                <p className="text-[14px] font-semibold tracking-[-0.015em] text-hud-paper">选择职业</p>
              </div>

              <div className="max-h-[min(56vh,440px)] space-y-1.5 overflow-y-auto p-2.5 [scrollbar-width:thin]">
                {ROLES.map((role) => {
                  const active = selectedClass === role.id
                  const RIcon = role.Icon
                  return (
                    <button
                      key={role.id}
                      type="button"
                      ref={(el) => {
                        roleItemRefs.current[role.id] = el
                      }}
                      onClick={() => {
                        setSelectedClass(role.id)
                        const el = roleItemRefs.current[role.id]
                        if (el) {
                          try {
                            el.scrollIntoView({ block: "nearest", behavior: reduce ? "auto" : "smooth" })
                          } catch {
                            /* ignore */
                          }
                        }
                      }}
                      aria-pressed={active}
                      className={`group/role relative flex w-full items-center gap-3 border px-3 py-2.5 text-left transition-colors duration-150 focus-visible:outline-none ${
                        active
                          ? "border-hud-accent/55 bg-hud-accent/12"
                          : "border-transparent hover:border-hud-line hover:bg-white/[0.03]"
                      }`}
                    >
                      {active ? <span className="absolute left-0 top-0 h-full w-[2px] bg-hud-accent" /> : null}
                      <span
                        className={`flex h-9 w-9 shrink-0 items-center justify-center border ${
                          active ? "border-hud-accent/45 text-hud-accent" : "border-hud-line text-hud-text-dim"
                        }`}
                      >
                        <RIcon className="h-4 w-4" strokeWidth={1.5} />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span
                          className={`block text-[14px] font-medium leading-tight tracking-[-0.015em] ${
                            active ? "text-hud-paper" : "text-hud-text"
                          }`}
                        >
                          {role.name}
                        </span>
                        <span className="mt-1 block truncate text-[12px] text-hud-text-dim">{role.tagline}</span>
                      </span>
                      {active ? (
                        <span className="shrink-0 font-mono-data text-[10px] uppercase tracking-[0.16em] text-hud-accent">
                          已选
                        </span>
                      ) : (
                        <Hud.HudChevronRight
                          className="h-3.5 w-3.5 shrink-0 text-hud-text-faint transition-transform duration-200 group-hover/role:translate-x-0.5"
                          strokeWidth={1.75}
                        />
                      )}
                    </button>
                  )
                })}
              </div>
            </section>
          </div>
        </motion.section>

        {/* 页尾遥测收边 */}
        <div className="mt-12 flex items-center gap-3 sm:mt-16">
          <span className="h-px flex-1 bg-gradient-to-r from-transparent to-hud-line-strong" />
          <span className="font-mono-data text-[10px] uppercase tracking-[0.28em] text-hud-text-faint">
            AsterNova · Deep Space Observatory
          </span>
          <span className="h-px flex-1 bg-gradient-to-l from-transparent to-hud-line-strong" />
        </div>
      </main>

      {/* ===== 移动端底部固定匹配条 ===== */}
      {/* 注意：音乐控件只有「顶栏」一个实例 —— 曾在此处再放一个，
          会导致两个 <audio> 同时播放同一首 BGM。 */}
      <div className="pointer-events-none fixed inset-x-0 bottom-0 z-50 flex justify-center border-t border-hud-line bg-ink-900/92 px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3 backdrop-blur-xl lg:hidden">
        <div className="pointer-events-auto w-full max-w-[min(100%,22rem)]">{matchButton("bar")}</div>
      </div>

      <LobbyAvatarPickerModal
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        currentId={avatarId}
        onSelect={setAvatarId}
      />
    </div>
  )
}
