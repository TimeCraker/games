"use client"

import * as React from "react"
import {
  Backpack,
  Crosshair,
  Lock,
  Radar,
  Shield,
  Sparkles,
  Swords,
  WandSparkles,
} from "lucide-react"

import { useCoreDefense } from "./state/coreDefenseContext"
import type { WeaponClass, WeaponInstance, WeaponLevel } from "./state/coreDefenseTypes"

function classIcon(classType: WeaponClass) {
  if (classType === "Warrior") return Swords
  if (classType === "Shooter") return Crosshair
  return WandSparkles
}

function renderClassIcon(classType: WeaponClass, className: string) {
  const Icon = classIcon(classType)
  return <Icon className={className} />
}

function weaponDisplayName(classType: WeaponClass, level: WeaponLevel) {
  const names: Record<WeaponClass, Record<WeaponLevel, string>> = {
    Warrior: { 1: "动能光剑", 2: "脉冲战刃", 3: "星穹裂界刃", 4: "王冠奇点圣剑" },
    Mage: { 1: "星尘法杖", 2: "新星共振杖", 3: "天穹超弦法典", 4: "紫曜星核权杖" },
    Shooter: { 1: "脉冲手枪", 2: "磁轨连发枪", 3: "苍穹湮灭狙", 4: "量子日冕歼星炮" },
  }
  return names[classType][level]
}

function levelGlow(level: WeaponLevel) {
  if (level === 1) return "border-zinc-200/60 shadow-[0_0_14px_rgba(255,255,255,0.18)]"
  if (level === 2) return "border-sky-400/70 shadow-[0_0_16px_rgba(56,189,248,0.35)]"
  if (level === 3) return "border-pink-400/70 shadow-[0_0_18px_rgba(244,114,182,0.42)]"
  return "border-violet-500/75 shadow-[0_0_20px_rgba(139,92,246,0.55)]"
}

type SlotMode = "equipped" | "inventory"

function WeaponSlot({
  weapon,
  mode,
}: {
  weapon: WeaponInstance | null
  mode: SlotMode
}) {
  const { dispatch } = useCoreDefense()
  const [menuOpen, setMenuOpen] = React.useState(false)

  if (!weapon) {
    return (
      <div className="relative h-24 w-24 rounded-2xl border border-dashed border-white/20 bg-black/45 shadow-[inset_0_0_18px_rgba(0,0,0,0.55)]">
        <div className="absolute inset-0 flex items-center justify-center">
          <Lock className="h-4 w-4 text-white/30" />
        </div>
      </div>
    )
  }

  const sellAction = mode === "inventory" ? "SELL_INVENTORY_WEAPON" : "SELL_EQUIPPED_WEAPON"

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setMenuOpen((v) => !v)}
        className={`group relative h-24 w-24 rounded-2xl border bg-black/55 p-1.5 backdrop-blur-md ${levelGlow(weapon.level)}`}
      >
        <div className="absolute left-1.5 top-1.5 rounded-md bg-black/55 px-1 text-[10px] font-bold text-white/90">Lv{weapon.level}</div>
        <div className="flex h-full items-center justify-center rounded-xl border border-white/10 bg-white/[0.03]">
          {renderClassIcon(weapon.classType, "h-9 w-9 text-white drop-shadow-[0_0_12px_rgba(255,255,255,0.4)]")}
        </div>
      </button>

      {menuOpen ? (
        <div className="absolute left-0 top-[104px] z-20 w-40 rounded-xl border border-white/15 bg-black/80 p-2 text-xs backdrop-blur-xl">
          <p className="mb-2 truncate text-white/80">{weaponDisplayName(weapon.classType, weapon.level)}</p>
          {mode === "inventory" ? (
            <button
              type="button"
              onClick={() => {
                dispatch({ type: "EQUIP_WEAPON", weaponId: weapon.id })
                setMenuOpen(false)
              }}
              className="mb-1 w-full rounded-lg border border-white/20 px-2 py-1 text-left text-white hover:bg-white/10"
            >
              装备
            </button>
          ) : (
            <button
              type="button"
              onClick={() => {
                dispatch({ type: "UNEQUIP_WEAPON", weaponId: weapon.id })
                setMenuOpen(false)
              }}
              className="mb-1 w-full rounded-lg border border-white/20 px-2 py-1 text-left text-white hover:bg-white/10"
            >
              卸下
            </button>
          )}
          <button
            type="button"
            onClick={() => {
              dispatch({ type: sellAction, weaponId: weapon.id })
              setMenuOpen(false)
            }}
            className="w-full rounded-lg border border-rose-300/35 px-2 py-1 text-left text-rose-100 hover:bg-rose-400/20"
          >
            出售 {weapon.sellPrice ?? "X"}
          </button>
        </div>
      ) : null}
    </div>
  )
}

export function InventoryUI() {
  const { state } = useCoreDefense()

  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-5 shadow-[0_8px_32px_0_rgba(0,0,0,0.3)] backdrop-blur-2xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.28em] text-white/45">Loadout</p>
          <h3 className="mt-1 text-xl font-semibold tracking-[-0.02em] text-white">装备与背包</h3>
        </div>
        <div className="flex items-center gap-2 text-xs text-white/65">
          <Sparkles className="h-4 w-4" />
          自动合成已启用
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-white/15 bg-black/30 px-3 py-1 text-xs text-white/80">
            <Shield className="h-3.5 w-3.5" />
            装备栏
          </div>
          <div className="grid grid-cols-3 gap-2">
            {Array.from({ length: state.equippedSlots }).map((_, idx) => (
              <WeaponSlot key={`equip-slot-${idx}`} weapon={state.equipped[idx] ?? null} mode="equipped" />
            ))}
          </div>
        </div>

        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-white/15 bg-black/30 px-3 py-1 text-xs text-white/80">
            <Backpack className="h-3.5 w-3.5" />
            背包
          </div>
          <div className="grid grid-cols-3 gap-2">
            {Array.from({ length: state.inventorySlots }).map((_, idx) => (
              <WeaponSlot key={`inventory-slot-${idx}`} weapon={state.inventory[idx] ?? null} mode="inventory" />
            ))}
          </div>
        </div>
      </div>

      <div className="mt-5 rounded-2xl border border-white/10 bg-black/35 p-3 text-xs text-white/70">
        <p className="mb-2 inline-flex items-center gap-1 font-semibold text-white/85">
          <Swords className="h-3.5 w-3.5 text-pink-200" />
          当前战斗构筑
        </p>
        <div className="flex flex-wrap gap-1.5">
          {state.equipped.map((weapon) => (
            <span key={weapon.id} className="inline-flex items-center gap-1 rounded-full bg-white/10 px-2 py-1">
              <Radar className="h-3 w-3 text-sky-200" />
              {weaponDisplayName(weapon.classType, weapon.level)}
            </span>
          ))}
          {!state.equipped.length ? <span className="text-white/45">尚未装备武器</span> : null}
        </div>
      </div>
    </section>
  )
}
