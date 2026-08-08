"use client"

import {
  Coins,
  Crosshair,
  Radar,
  RefreshCcw,
  Sparkles,
  Swords,
  WandSparkles,
} from "lucide-react"

import { useCoreDefense } from "./state/coreDefenseContext"
import { getRollTableByMaxLevel } from "./state/shopPool"
import type { WeaponClass, WeaponLevel } from "./state/coreDefenseTypes"

function classIcon(classType: WeaponClass) {
  if (classType === "Warrior") return Swords
  if (classType === "Shooter") return Crosshair
  return WandSparkles
}

function classLabel(classType: WeaponClass) {
  if (classType === "Warrior") return "战士"
  if (classType === "Shooter") return "射手"
  return "法师"
}

function weaponDisplayName(classType: WeaponClass, level: WeaponLevel) {
  const names: Record<WeaponClass, Record<WeaponLevel, string>> = {
    Warrior: { 1: "动能光剑", 2: "脉冲战刃", 3: "星穹裂界刃", 4: "王冠奇点圣剑" },
    Mage: { 1: "星尘法杖", 2: "新星共振杖", 3: "天穹超弦法典", 4: "紫曜星核权杖" },
    Shooter: { 1: "脉冲手枪", 2: "磁轨连发枪", 3: "苍穹湮灭狙", 4: "量子日冕歼星炮" },
  }
  return names[classType][level]
}

export function ShopUI() {
  const { state, dispatch } = useCoreDefense()

  const maxLevel = [...state.inventory, ...state.equipped].reduce<WeaponLevel>(
    (acc, weapon) => (weapon.level > acc ? weapon.level : acc),
    1,
  )
  const probability = getRollTableByMaxLevel(maxLevel)

  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-5 shadow-[0_8px_32px_0_rgba(0,0,0,0.3)] backdrop-blur-2xl">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.28em] text-white/45">Weapon Bay</p>
          <h2 className="mt-1 text-2xl font-semibold tracking-[-0.02em] text-white">AsterNova Shop</h2>
        </div>
        <button
          type="button"
          onClick={() => dispatch({ type: "REFRESH_SHOP" })}
          className="group inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/[0.05] px-4 py-2 text-sm font-semibold text-white/90 transition hover:scale-[1.03] hover:border-pink-300/50 hover:bg-gradient-to-r hover:from-pink-300/85 hover:to-purple-600/85 hover:text-black"
        >
          <RefreshCcw className="h-4 w-4 transition-transform duration-300 group-hover:rotate-180" />
          <Coins className="h-4 w-4" />
          刷新 - {state.refreshCost}
        </button>
      </div>

      <div className="mb-5 rounded-2xl border border-white/10 bg-black/25 p-3">
        <p className="mb-2 text-xs text-white/65">出货概率池</p>
        <div className="flex h-2.5 overflow-hidden rounded-full border border-white/10 bg-black/30 shadow-[0_0_24px_rgba(180,120,255,0.24)]">
          {probability.map((item) => (
            <div
              key={item.label}
              className={item.colorClass}
              style={{ width: `${item.weight}%`, boxShadow: "0 0 14px rgba(255,255,255,0.25)" }}
            />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {state.shopOffers.map((offer) => {
          const ClassIcon = classIcon(offer.weapon.classType)
          return (
            <article
              key={offer.id}
              className="group flex h-[370px] flex-col overflow-hidden rounded-3xl border border-white/10 bg-white/[0.04] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.12)] backdrop-blur-xl"
            >
              <div className="relative mb-3 flex-[0_0_60%] overflow-hidden rounded-2xl border border-white/15 bg-black/40 backdrop-blur-md">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_10%,rgba(236,72,153,0.25),transparent_52%)]" />
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_100%,rgba(139,92,246,0.3),transparent_60%)]" />
                <div className="absolute right-2 top-2 rounded-full border border-white/20 bg-black/35 px-2 py-0.5 text-[10px] font-semibold text-white/80">
                  Lv{offer.weapon.level}
                </div>
                <div className="relative z-[1] flex h-full items-center justify-center">
                  <ClassIcon className="h-20 w-20 text-white drop-shadow-[0_0_18px_rgba(255,255,255,0.35)]" strokeWidth={1.5} />
                </div>
              </div>

              <div className="flex flex-1 flex-col">
                <p className="text-base font-semibold tracking-[-0.02em] text-white">
                  {weaponDisplayName(offer.weapon.classType, offer.weapon.level)}
                </p>
                <p className="mt-0.5 text-xs text-white/60">{classLabel(offer.weapon.classType)}</p>
                <div className="mt-2 flex flex-wrap gap-1.5 text-[11px] text-white/75">
                  <span className="inline-flex items-center gap-1 rounded-full bg-white/10 px-2 py-1">
                    <Swords className="h-3 w-3 text-pink-200" />
                    {offer.weapon.baseDamage}
                  </span>
                  <span className="inline-flex items-center gap-1 rounded-full bg-white/10 px-2 py-1">
                    <Radar className="h-3 w-3 text-sky-200" />
                    {offer.weapon.attackRange}
                  </span>
                  <span className="inline-flex items-center gap-1 rounded-full bg-white/10 px-2 py-1">
                    <Sparkles className="h-3 w-3 text-violet-200" />
                    {offer.weapon.cooldownMs}ms
                  </span>
                </div>

                <button
                  type="button"
                  onClick={() => dispatch({ type: "BUY_WEAPON", offerId: offer.id })}
                  className="mt-auto inline-flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-pink-300 to-purple-600 px-4 py-2.5 text-sm font-semibold text-black transition duration-200 hover:scale-[1.03] hover:shadow-[0_0_22px_rgba(221,160,255,0.6)]"
                >
                  <Coins className="h-4 w-4" />
                  购买 {offer.weapon.buyPrice}
                </button>
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}
