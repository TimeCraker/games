"use client"

import * as React from "react"
import { AnimatePresence, motion } from "framer-motion"

import { ArcadeEntry } from "@/src/components/arcade/ArcadeEntry"
import { ArcadeResult } from "@/src/components/arcade/ArcadeResult"
import { useArcadeAccent } from "@/src/components/arcade/useArcadeAccent"
import { GameBackButton } from "@/src/components/ui/GameBackButton"
import { cn } from "@/lib/utils"

import { CLASSES, CLASS_IDS, DEFAULT_CLASS } from "./content/classes"
import { ESKILLS } from "./content/eskills"
import { WEAPONS } from "./content/weapons"
import { NebulaHost, type UiSnapshot } from "./render/host"
import { nebulaSfx } from "./render/NebulaSfx"
import type { ClassId } from "./sim/types"
import { readSave, writeSave } from "./save"
import { HudLoadout, HudRadar, HudScreenFx, HudSkillRing, HudStats, HudSysKeys, Panel } from "./ui/Hud"
import { Joystick } from "./ui/Joystick"
import { MONO, tierStyle } from "./ui/theme"

type Phase = "briefing" | "hangar" | "run" | "over"

const SKIP_KEY = "nebula-survivor-skip-rules"

const EMPTY_UI: UiSnapshot = {
  hp: 82, maxHp: 82, level: 1, xp: 0, xpToNext: 26, wave: 1, kills: 0, score: 0, coins: 0,
  time: 0, dps: 0, weapons: [], eskill: "blink", eskillCd: 0, eskillReady: true,
  shopOpen: false, gameOver: false, bossAlive: false, flash: 0, hurt: 0, radar: [],
}

export function NebulaGame() {
  useArcadeAccent("nebula-survivor")

  const stageRef = React.useRef<HTMLDivElement>(null)
  const hostRef = React.useRef<NebulaHost | null>(null)
  const [phase, setPhase] = React.useState<Phase>("briefing")
  const [classId, setClassId] = React.useState<ClassId>(DEFAULT_CLASS)
  const [ui, setUi] = React.useState<UiSnapshot>(EMPTY_UI)
  const [pauseOpen, setPauseOpen] = React.useState(false)
  const [helpOpen, setHelpOpen] = React.useState(false)
  const [sfxOn, setSfxOn] = React.useState(true)
  const [dontShow, setDontShow] = React.useState(false)
  const [runId, setRunId] = React.useState(0)
  const [isTouch, setIsTouch] = React.useState(false)

  /* ---------------- 首访：读跳过标记与存档 ---------------- */
  React.useEffect(() => {
    try {
      const save = readSave()
      setClassId(save.lastClass)
      if (localStorage.getItem(SKIP_KEY) === "1") setPhase("hangar")
      else setPhase("briefing")
    } catch { /* 隐私模式 → 保持默认 */ }
    setIsTouch(typeof window !== "undefined" && (("ontouchstart" in window) || (navigator.maxTouchPoints ?? 0) > 0))
  }, [])

  /* ---------------- 建档 / 启动一局 ---------------- */
  const startRun = React.useCallback((cid: ClassId) => {
    nebulaSfx.ensure() // 首次手势后恢复 AudioContext（autoplay 合规）
    writeSave((s) => { s.lastClass = cid; s.runs += 1 })
    setUi(EMPTY_UI)
    setRunId((n) => n + 1)
    setPhase("run")
  }, [])

  /* ---------------- 挂载 / 卸载 Pixi 宿主 ---------------- */
  React.useEffect(() => {
    if (phase !== "run") return
    const el = stageRef.current
    if (!el) return

    const save = readSave()
    const bonus = {
      damage: save.xp * 0.002,
      armor: Math.min(0.12, save.xp * 0.00035),
      spell: save.xp * 0.002,
      eskillLevel: save.eskills[CLASSES[classId].eskill] ?? 1,
      startWeaponStars: save.weaponStars,
    }
    const host = new NebulaHost({
      seed: (Date.now() ^ (runId * 2654435761)) >>> 0,
      classId,
      bonus,
      onUi: setUi,
    })
    hostRef.current = host
    const move = (x: number, y: number) => host.setMove(x, y)

    void host.mount(el).then(() => {
      // 挂好后立刻推一帧 UI，避免 HUD 空白
      setUi(host.snapshot())
    })

    /* ---- 键盘输入 ---- */
    const keys = new Set<string>()
    const dir = () => {
      let x = 0, y = 0
      if (keys.has("a") || keys.has("arrowleft")) x -= 1
      if (keys.has("d") || keys.has("arrowright")) x += 1
      if (keys.has("w") || keys.has("arrowup")) y -= 1
      if (keys.has("s") || keys.has("arrowdown")) y += 1
      return { x, y }
    }
    const onKeyDown = (e: KeyboardEvent) => {
      const k = e.key.toLowerCase()
      if (k === "e") { host.useESkill(); e.preventDefault(); return }
      if (k === "p" || k === "escape") { setPauseOpen((v) => !v); e.preventDefault(); return }
      keys.add(k)
      const d = dir(); move(d.x, d.y)
    }
    const onKeyUp = (e: KeyboardEvent) => {
      keys.delete(e.key.toLowerCase())
      const d = dir(); move(d.x, d.y)
    }
    window.addEventListener("keydown", onKeyDown)
    window.addEventListener("keyup", onKeyUp)

    return () => {
      window.removeEventListener("keydown", onKeyDown)
      window.removeEventListener("keyup", onKeyUp)
      host.destroy()
      hostRef.current = null
    }
  }, [phase, classId, runId])

  /* ---------------- 死亡 → 结算 + 落盘 ---------------- */
  React.useEffect(() => {
    if (phase !== "run" || !ui.gameOver) return
    const host = hostRef.current
    if (host) {
      const s = host.sim
      writeSave((sv) => {
        sv.coins += s.coins
        sv.xp += Math.round(s.score / 12)
        sv.totalKills += s.kills
      })
    }
    const t = window.setTimeout(() => setPhase("over"), 900)
    return () => window.clearTimeout(t)
  }, [phase, ui.gameOver])

  /* ---------------- 商店：波次节点自动开启 ---------------- */
  const shopOpen = phase === "run" && ui.shopOpen && !ui.gameOver

  const onBriefingConfirm = React.useCallback(() => {
    try { if (dontShow) localStorage.setItem(SKIP_KEY, "1") } catch { /* ignore */ }
    setPhase("hangar")
  }, [dontShow])

  const closePause = React.useCallback(() => setPauseOpen(false), [])
  const cls = CLASSES[classId]

  return (
    <div className="relative flex h-dvh min-h-0 flex-col overflow-hidden bg-space-black text-white">
      {/* ============ 游玩区（全屏自适应，绝不放进 scale 容器） ============ */}
      <div ref={stageRef} className="absolute inset-0" aria-hidden />

      {/* ============ HUD ============ */}
      <div className={cn("pointer-events-none absolute inset-0 z-10", (pauseOpen || helpOpen || shopOpen) && "invisible")}>
        <HudScreenFx ui={ui} />

        {/* 中上 · 品牌 */}
        <div className="absolute left-1/2 top-2.5 -translate-x-1/2 text-center sm:top-3.5">
          <div className="text-[9.5px] font-bold tracking-[0.16em] text-white/85 sm:text-[11px]">NEBULA SURVIVOR</div>
          <div className="text-[8px] tracking-[0.3em] text-hud-accent sm:text-[9px]">星 域 突 围</div>
        </div>

        {/* 左上 · 生存数据 */}
        <div className="absolute left-2 top-12 sm:left-4 sm:top-14">
          <HudStats ui={ui} />
        </div>

        {/* 右上 · 系统键 + 雷达 */}
        <div className="absolute right-2 top-2.5 flex flex-col items-end gap-2 sm:right-4 sm:top-3.5">
          <HudSysKeys
            sfxOn={sfxOn}
            onToggleSfx={() => { const n = !sfxOn; setSfxOn(n); nebulaSfx.volume = n ? 0.6 : 0; }}
            onPause={() => setPauseOpen(true)}
            onHelp={() => setHelpOpen(true)}
          />
          <div className="hidden sm:block"><HudRadar ui={ui} size={112} /></div>
        </div>

        {/* 底部中央 · 武器槽 */}
        <div className="absolute bottom-3 left-1/2 -translate-x-1/2 sm:bottom-4">
          <HudLoadout ui={ui} />
        </div>

        {/* 右下 · E 技（触屏时它本身就是按钮，不再额外画一个 E 键） */}
        <div className="absolute bottom-3 right-2.5 z-20 sm:bottom-4 sm:right-4">
          <HudSkillRing ui={ui} size={isTouch ? 58 : 62} onUse={isTouch ? () => hostRef.current?.useESkill() : undefined} />
        </div>

        {/* 左下 · 摇杆（仅触屏） */}
        {isTouch ? (
          <div className="pointer-events-auto absolute bottom-3 left-2.5 z-20 sm:bottom-5 sm:left-5">
            <Joystick onChange={(x, y) => hostRef.current?.setMove(x, y)} size={isTouch ? 100 : 116} />
          </div>
        ) : null}

        {/* 左上返回（桌面） */}
        <div className="pointer-events-auto absolute left-2 top-2.5 sm:left-4 sm:top-3.5">
          <GameBackButton variant="header" label="大厅" />
        </div>


      </div>

      {/* ============ 商店（波次节点） ============ */}
      <AnimatePresence>
        {shopOpen ? (
          <ShopOverlay
            ui={ui}
            classId={classId}
            onBuy={(id) => hostRef.current?.sim.buyWeapon(id)}
            onUpgrade={(id) => hostRef.current?.sim.upgradeWeapon(id)}
            onRefresh={() => { hostRef.current?.sim.refreshShop(); setUi(hostRef.current!.snapshot()) }}
            onClose={() => { hostRef.current?.sim.closeShop(); setUi(hostRef.current!.snapshot()) }}
          />
        ) : null}
      </AnimatePresence>

      {/* ============ 弹层 ============ */}
      {phase === "briefing" ? (
        <ArcadeEntry
          slug="nebula-survivor"
          titleId="nebula-briefing-title"
          eyebrow={<p className={`mb-1 text-center text-[10px] uppercase tracking-[0.32em] text-white/45 ${MONO}`}>Briefing</p>}
          title="星域突围"
          subtitle={<span className="text-[13px] text-white/55">读完点击「进入机库」开始</span>}
          label="进入机库"
          onConfirm={onBriefingConfirm}
          skipRules={{ checked: dontShow, onChange: setDontShow, label: "下次不再显示（本机记住）" }}
        >
          <BriefingRules />
        </ArcadeEntry>
      ) : null}

      {pauseOpen ? (
        <ArcadeEntry
          slug="nebula-survivor"
          titleId="nebula-pause-title"
          eyebrow={<p className={`mb-1 text-center text-[10px] uppercase tracking-[0.32em] text-white/45 ${MONO}`}>Paused</p>}
          title="已暂停"
          subtitle={<span className="text-[13px] text-white/55">关闭后继续战斗（Esc / P 亦可）</span>}
          label="继续游戏"
          onConfirm={closePause}
          onRequestClose={closePause}
        >
          <BriefingRules />
        </ArcadeEntry>
      ) : null}

      {helpOpen ? (
        <ArcadeEntry
          slug="nebula-survivor"
          titleId="nebula-help-title"
          eyebrow={<p className={`mb-1 text-center text-[10px] uppercase tracking-[0.32em] text-white/45 ${MONO}`}>Reference</p>}
          title="行动手册"
          subtitle={<span className="text-[13px] text-white/55">随时可查</span>}
          label="返回游戏"
          onConfirm={() => setHelpOpen(false)}
          onRequestClose={() => setHelpOpen(false)}
        >
          <BriefingRules />
        </ArcadeEntry>
      ) : null}

      {phase === "hangar" ? (
        <HangarPanel
          classId={classId}
          onPick={setClassId}
          onLaunch={() => startRun(classId)}
        />
      ) : null}

      <AnimatePresence>
        {phase === "over" ? (
          <ArcadeResult
            slug="nebula-survivor"
            score={ui.score}
            mode={cls.name}
            title={ui.score >= 3000 ? "任务达成" : "信号丢失"}
            subtitle={`${cls.name} · 存活 ${formatTime(ui.time)}`}
            extraStats={[
              { label: "击杀", value: String(ui.kills) },
              { label: "存活", value: formatTime(ui.time) },
              { label: "波次", value: String(ui.wave) },
              { label: "等级", value: String(ui.level) },
            ]}
            actionLabel="返回机库"
            onAction={() => setPhase("hangar")}
          />
        ) : null}
      </AnimatePresence>
    </div>
  )
}

/* ============================ 子视图 ============================ */

function BriefingRules() {
  const rows = [
    { t: "移动", d: "WASD / 方向键；触屏用左下摇杆。攻击全自动，你只负责走位。" },
    { t: "构筑", d: "打怪掉武器与金币；3 个同名同星武器自动合成升 1 星，也可花金币直升。" },
    { t: "E 技", d: "每个职业一个专属 E 技（走位/生存向），右下环显示冷却。" },
    { t: "撤离", d: "每波结束开商店；随时可撤，不强制击杀 Boss。" },
  ]
  return (
    <ul className="mt-4 flex flex-col gap-2">
      {rows.map((r) => (
        <li key={r.t} className="rounded-2xl border border-white/[0.08] bg-white/[0.04] px-3.5 py-2.5">
          <p className="text-[12.5px] font-semibold text-white/90">{r.t}</p>
          <p className="mt-0.5 text-[11.5px] leading-relaxed text-white/55">{r.d}</p>
        </li>
      ))}
    </ul>
  )
}

function HangarPanel({ classId, onPick, onLaunch }: { classId: ClassId; onPick: (c: ClassId) => void; onLaunch: () => void }) {
  const save = React.useMemo(() => readSave(), [])
  return (
    <div
      className="absolute inset-0 z-30 overflow-y-auto overscroll-contain px-3 py-4 backdrop-blur-md"
      style={{ background: "rgba(5,6,7,0.72)" }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="nebula-hangar-title"
    >
      <div className="mx-auto w-full max-w-[880px]">
        <p className={`text-[10px] uppercase tracking-[0.32em] text-white/45 ${MONO}`}>Hangar</p>
        <h2 id="nebula-hangar-title" className="mt-1 text-xl font-semibold tracking-tight text-white">机库 · 选择机型</h2>
        <p className="mt-1 text-[12px] text-white/50">
          金币 <b className="text-hud-accent-bright">{save.coins}</b> · 经验 <b className="text-hud-accent-bright">{save.xp}</b>
        </p>

        <div className="mt-4 grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
          {CLASS_IDS.map((id) => {
            const c = CLASSES[id]
            const active = id === classId
            return (
              <button
                key={id}
                type="button"
                onClick={() => onPick(id)}
                className={cn(
                  "relative rounded-xl border p-3 text-left transition",
                  active ? "border-hud-accent/70 bg-hud-accent/[0.08]" : "border-white/10 bg-white/[0.03] hover:bg-white/[0.06]",
                )}
              >
                <div className="flex items-baseline justify-between">
                  <span className="text-[13px] font-semibold text-white/92">{c.name}</span>
                  <span className={`text-[9.5px] text-white/45 ${MONO}`}>HP {c.maxHp}</span>
                </div>
                <p className="mt-0.5 text-[11px] text-hud-accent/85">{c.role}</p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {c.weapons.map((w) => (
                    <span key={w} className="rounded border border-white/12 bg-black/40 px-1.5 py-0.5 text-[9.5px] text-white/70">
                      {WEAPONS[w].name}
                    </span>
                  ))}
                </div>
                <p className="mt-2 text-[10px] text-white/45">
                  E 技 · <span className="text-white/75">{ESKILLS[c.eskill].name}</span>
                </p>
              </button>
            )
          })}
        </div>

        <button
          type="button"
          onClick={onLaunch}
          className="mt-5 w-full rounded-2xl bg-gradient-to-r from-amber-400 via-amber-500 to-amber-600 py-3.5 text-[15px] font-semibold text-gray-950 shadow-lg shadow-amber-500/20 transition hover:brightness-105 active:scale-[0.99]"
        >
          出击 · {CLASSES[classId].name}
        </button>
      </div>
    </div>
  )
}

function ShopOverlay({ ui, classId, onBuy, onUpgrade, onRefresh, onClose }: {
  ui: UiSnapshot
  classId: ClassId
  onBuy: (id: never) => void
  onUpgrade: (id: never) => void
  onRefresh: () => void
  onClose: () => void
}) {
  const offers = CLASSES[classId].weapons
  return (
    <motion.div
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="absolute inset-0 z-30 flex items-center justify-center px-3 backdrop-blur-md"
      style={{ background: "rgba(5,6,7,0.72)" }}
      role="dialog" aria-modal="true" aria-labelledby="nebula-shop-title"
    >
      <Panel className="w-full max-w-[520px] p-4 sm:p-5">
        <p className={`text-[10px] uppercase tracking-[0.32em] text-white/45 ${MONO}`}>Supply</p>
        <h2 id="nebula-shop-title" className="mt-1 text-lg font-semibold text-white">补给站</h2>
        <p className="mt-1 text-[12px] text-white/50">
          金币 <b className="text-hud-accent-bright">{ui.coins}</b> · 波次 {ui.wave}
        </p>

        {/* 本职业可买的三把武器 */}
        <div className="mt-3 grid grid-cols-1 gap-2">
          {offers.map((id) => {
            const owned = ui.weapons.find((w) => w.id === id)
            return (
              <div key={id} className="flex items-center justify-between rounded-lg px-2.5 py-2" style={tierStyle(owned?.stars ?? 1)}>
                <div className="min-w-0">
                  <p className="text-[11.5px] font-semibold text-white/90">{WEAPONS[id].name}</p>
                  <p className="truncate text-[10px] text-white/45">
                    {owned ? `已持有 ★${owned.stars} · ${owned.mergeCount}/3` : WEAPONS[id].blurb}
                  </p>
                </div>
                <div className="flex shrink-0 gap-1.5">
                  {owned ? (
                    <button
                      type="button"
                      className="rounded border border-white/15 bg-black/40 px-2 py-1 text-[10.5px] text-white/85 hover:bg-white/10"
                      onClick={() => onUpgrade(id as never)}
                    >
                      直升 1 星
                    </button>
                  ) : null}
                  <button
                    type="button"
                    className="rounded border border-hud-accent/45 bg-hud-accent/12 px-2 py-1 text-[10.5px] text-hud-accent-bright hover:bg-hud-accent/20"
                    onClick={() => onBuy(id as never)}
                  >
                    购买
                  </button>
                </div>
              </div>
            )
          })}
        </div>

        <div className="mt-3 flex gap-2">
          <button type="button" className="flex-1 rounded-lg border border-white/15 bg-white/[0.05] py-2 text-[12px] text-white/85 hover:bg-white/10" onClick={onRefresh}>
            刷新货架
          </button>
          <button
            type="button"
            className="flex-1 rounded-lg bg-gradient-to-r from-amber-400 to-amber-600 py-2 text-[12.5px] font-semibold text-gray-950"
            onClick={onClose}
          >
            继续战斗
          </button>
        </div>
        <p className="mt-2 text-[10px] text-white/35">
          提示：商店货架与「直接花钱升星」都只作用于当前持有的武器。
        </p>
      </Panel>
    </motion.div>
  )
}

function formatTime(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, "0")}`
}
