"use client"

import * as React from "react"

import { ESKILLS } from "../content/eskills"
import { WEAPONS } from "../content/weapons"
import type { ESkillId, WeaponId } from "../sim/types"
import type { UiSnapshot } from "../render/host"
import { MONO, hexToRgba, tierOf, tierStyle } from "./theme"

/** 面板通用：玻璃 + 四角括号（遥测台语言，与主站同一套母题） */
export function Panel({ className = "", children, style }: { className?: string; children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div
      className={`relative rounded-xl border border-white/10 bg-[rgba(24,27,31,0.72)] shadow-[0_16px_48px_-12px_rgba(0,0,0,0.7),inset_0_1px_0_rgba(255,255,255,0.06)] backdrop-blur-md ${className}`}
      style={style}
    >
      <span className="pointer-events-none absolute -left-px -top-px h-2.5 w-2.5 border-l border-t border-hud-accent/65" />
      <span className="pointer-events-none absolute -bottom-px -right-px h-2.5 w-2.5 border-b border-r border-hud-accent/65" />
      {children}
    </div>
  )
}

function Meter({ label, value, max, kind }: { label: string; value: number; max: number; kind: "hp" | "xp" }) {
  const pct = Math.max(0, Math.min(100, (value / Math.max(1, max)) * 100))
  return (
    <div className="flex items-center gap-2">
      <span className={`w-4 text-right text-[10px] font-semibold tracking-wider ${kind === "hp" ? "text-white/60" : "text-[#9CB86A]/75"} ${MONO}`}>{label}</span>
      <div className="h-[7px] flex-1 overflow-hidden rounded-full bg-white/[0.07]">
        <div
          className="h-full rounded-full transition-[width] duration-150"
          style={{
            width: `${pct}%`,
            background: kind === "hp"
              ? "linear-gradient(90deg,#8A6519,#D8A33C 55%,#E9BE69)"
              : "linear-gradient(90deg,#5F7D42,#9CB86A)",
          }}
        />
      </div>
      <span className={`w-11 text-right text-[10px] text-white/55 ${MONO}`}>{Math.round(value)}/{Math.round(max)}</span>
    </div>
  )
}

/** ① 生存数据（左上） */
export function HudStats({ ui }: { ui: UiSnapshot }) {
  return (
    <Panel className="w-[13.5rem] px-3 py-2.5 sm:w-56 sm:px-3.5">
      <div className="mb-2 flex items-baseline justify-between">
        <span className={`text-[12px] font-semibold tracking-[0.12em] text-white/85 ${MONO}`}>
          WAVE <span className="text-hud-accent-bright">{String(ui.wave).padStart(2, "0")}</span>
        </span>
        <span className={`text-[9.5px] uppercase tracking-[0.18em] text-white/45 ${MONO}`}>
          LV <span className="text-white/80">{ui.level}</span>
        </span>
      </div>
      <div className="flex flex-col gap-1.5">
        <Meter label="HP" value={ui.hp} max={ui.maxHp} kind="hp" />
        <Meter label="XP" value={ui.xp} max={ui.xpToNext} kind="xp" />
      </div>
      <div className={`mt-2 flex items-center justify-between border-t border-white/[0.07] pt-2 text-[9.5px] text-white/45 ${MONO}`}>
        <span>击杀 <b className="font-semibold text-white/85">{ui.kills}</b></span>
        <span className="h-3 w-px bg-white/10" />
        <span>得分 <b className="font-semibold text-hud-accent-bright">{ui.score}</b></span>
        <span className="h-3 w-px bg-white/10" />
        <span>威胁 <b className={`font-semibold ${ui.bossAlive ? "text-[#D98A72]" : "text-white/70"}`}>{ui.bossAlive ? "高" : ui.wave >= 4 ? "中" : "低"}</b></span>
      </div>
    </Panel>
  )
}

/** ③ 系统键（右上）：窄屏只留图标 */
export function HudSysKeys({ sfxOn, onToggleSfx, onPause, onHelp }: {
  sfxOn: boolean; onToggleSfx: () => void; onPause: () => void; onHelp: () => void
}) {
  const cls = "pointer-events-auto flex h-8 min-w-8 shrink-0 items-center justify-center gap-1.5 whitespace-nowrap rounded-full border border-white/13 bg-black/55 px-2.5 text-[11px] text-white/80 backdrop-blur-md transition hover:bg-white/[0.11] active:scale-[0.97] sm:px-3"
  return (
    <div className="pointer-events-none flex items-center gap-1.5">
      <button type="button" className={cls} aria-label={sfxOn ? "关闭音效" : "开启音效"} onClick={onToggleSfx}>
        <span className="text-[12px] leading-none">{sfxOn ? "◔" : "◕"}</span>
        <span className="hidden sm:inline">音效</span>
      </button>
      <button type="button" className={cls} aria-label="暂停" onClick={onPause}>
        <span className="text-[12px] leading-none">❙❙</span>
        <span className="hidden sm:inline">暂停</span>
      </button>
      <button type="button" className={cls} aria-label="规则" onClick={onHelp}>
        <span className="text-[12px] leading-none">?</span>
        <span className="hidden sm:inline">规则</span>
      </button>
    </div>
  )
}

/** ⑤ 环形雷达：把「威胁」从一个数字变成方位（白皮书 §11.8） */
export function HudRadar({ ui, size }: { ui: UiSnapshot; size: number }) {
  const r = size / 2
  return (
    <div
      className="pointer-events-none relative rounded-full border"
      style={{
        width: size, height: size,
        borderColor: "rgba(216,163,60,0.22)",
        background: "radial-gradient(circle, rgba(216,163,60,0.05) 0%, rgba(5,6,7,0.5) 70%)",
      }}
    >
      <span className="absolute rounded-full border border-hud-accent/12" style={{ inset: "22%" }} />
      <span className="absolute rounded-full border border-hud-accent/16" style={{ inset: "44%" }} />
      <span className="absolute left-1/2 top-[6%] bottom-[6%] w-px bg-hud-accent/12" />
      <span className="absolute top-1/2 left-[6%] right-[6%] h-px bg-hud-accent/12" />
      <span
        className="absolute inset-0 rounded-full"
        style={{
          background: "conic-gradient(from 0deg, rgba(216,163,60,0.30), transparent 26%, transparent 100%)",
          animation: "nebula-sweep 2.6s linear infinite",
        }}
      />
      <span className="absolute left-1/2 top-1/2 h-[5px] w-[5px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#F2D79B] shadow-[0_0_8px_2px_rgba(242,215,155,0.6)]" />
      {ui.radar.map((b, i) => {
        const dist = b.d * (r - 6)
        const x = r + Math.cos(b.a) * dist
        const y = r + Math.sin(b.a) * dist
        const color = b.kind === "boss" ? "#C0503A" : b.kind === "heavy" ? "#C0503A" : b.kind === "drone" ? "#7FB39E" : "#C08069"
        return (
          <span
            key={i}
            className="absolute rounded-full"
            style={{
              left: x, top: y, width: b.kind === "boss" ? 6 : 4, height: b.kind === "boss" ? 6 : 4,
              marginLeft: b.kind === "boss" ? -3 : -2, marginTop: b.kind === "boss" ? -3 : -2,
              background: color, boxShadow: `0 0 6px ${color}`,
            }}
          />
        )
      })}
    </div>
  )
}

/** ⑦ 底部中央 · 武器槽（品级工艺 + 星数 + 三合一刻痕）*/
export function HudLoadout({ ui }: { ui: UiSnapshot }) {
  const slots = [...ui.weapons]
  while (slots.length < 3) slots.push(null as never)
  return (
    <div className="pointer-events-none flex items-end gap-1.5 sm:gap-2.5">
      {slots.slice(0, 3).map((w, i) => {
        if (!w) {
          return (
            <div
              key={i}
              className="w-[60px] rounded-lg border border-dashed border-white/14 bg-black/45 px-1.5 py-1.5 backdrop-blur-md sm:w-[84px] sm:px-2.5 sm:py-2"
            >
              <div className="mb-1 text-[9px] text-white/40 sm:text-[10px]">空槽</div>
              <div className="flex gap-1">
                {[0, 1, 2].map((k) => <span key={k} className="h-[3px] w-3.5 rounded-sm bg-white/10" />)}
              </div>
            </div>
          )
        }
        const def = WEAPONS[w.id as WeaponId]
        const tier = tierOf(w.stars)
        return (
          <div key={i} className="w-[60px] rounded-lg px-1.5 py-1.5 backdrop-blur-md sm:w-[84px] sm:px-2.5 sm:py-2" style={tierStyle(w.stars)}>
            <div className="mb-1 truncate text-[9px] font-semibold text-white/90 sm:text-[10px]">{def?.name ?? w.id}</div>
            <div className="mb-1 flex gap-[2px]" style={{ color: tier.hex }}>
              {[1, 2, 3, 4, 5].map((s) => (
                <span key={s} className="h-1.5 w-1.5 rotate-45" style={{ background: s <= w.stars ? tier.hex : "rgba(255,255,255,0.16)" }} />
              ))}
            </div>
            <div className="flex items-center gap-[3px]">
              {[1, 2, 3].map((n) => (
                <span key={n} className="h-[3px] w-2.5 rounded-sm sm:w-3.5" style={{ background: n <= w.mergeCount ? tier.hex : "rgba(255,255,255,0.14)" }} />
              ))}
              <span className={`ml-0.5 text-[8.5px] text-white/45 ${MONO}`}>{w.mergeCount}/3</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

/** ⑧ 右下 · E 技冷却环 */
export function HudSkillRing({ ui, size = 64, onUse }: { ui: UiSnapshot; size?: number; onUse?: () => void }) {
  const def = ESKILLS[ui.eskill as ESkillId]
  const total = def?.cd ?? 1
  const k = ui.eskillCd <= 0 ? 1 : 1 - Math.min(1, ui.eskillCd / total)
  const Tag = onUse ? "button" : "div"
  return (
    <Tag
      type={onUse ? "button" : undefined}
      onClick={onUse}
      className={`${onUse ? "pointer-events-auto active:scale-95" : "pointer-events-none"} relative rounded-full transition`}
      style={{
        width: size, height: size,
        background: `conic-gradient(rgba(216,163,60,0.95) ${k * 360}deg, rgba(255,255,255,0.09) ${k * 360}deg 360deg)`,
      }}
      aria-label={`E 技 ${def?.name ?? ""}`}
    >
      <div
        className="absolute rounded-full border border-hud-accent/35 bg-[rgba(10,11,13,0.92)]"
        style={{ inset: 5, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 1 }}
      >
        <span className={`text-[9px] font-bold tracking-wider ${k >= 1 ? "text-hud-accent-bright" : "text-white/45"}`}>E</span>
        <span className={`text-[12px] font-semibold ${k >= 1 ? "text-hud-accent-bright" : "text-white/60"} ${MONO}`}>
          {k >= 1 ? (def?.name ?? "").slice(0, 2) : ui.eskillCd.toFixed(1)}
        </span>
      </div>
    </Tag>
  )
}

/** 全屏反馈：升级闪光 / 受击红晕 */
export function HudScreenFx({ ui }: { ui: UiSnapshot }) {
  return (
    <>
      <div
        className="pointer-events-none absolute inset-0 transition-opacity duration-150"
        style={{ background: "rgba(242,215,155,0.9)", opacity: Math.min(0.32, ui.flash * 0.32) }}
      />
      <div
        className="pointer-events-none absolute inset-0 transition-opacity duration-200"
        style={{ background: `radial-gradient(ellipse 76% 66% at 50% 48%, transparent 46%, ${hexToRgba("#C0503A", 0.34)} 100%)`, opacity: Math.min(1, ui.hurt) }}
      />
    </>
  )
}
