"use client"

import * as React from "react"
import { LiquidBar } from "@/src/components/ui/LiquidBar"

/**
 * Arena 战斗 HUD 组件（从 app/arena/page.tsx 内联 style 抽离）
 * 保留原有视觉：skew 液体血条 / 能量条 / 大招 Q 键波纹
 */

type Side = "left" | "right"

const WAVE_MASK =
  'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 1200 120\' preserveAspectRatio=\'none\'%3E%3Cpath d=\'M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V120H282.65C297.82,95.68,307.39,73.19,321.39,56.44Z\' style=\'fill:%23000;\'%3E%3C/path%3E%3C/svg%3E")'

/** 血条（skew 液体） */
export function HpBar({ hp, side }: { hp: number; side: Side }) {
  return <LiquidBar value={hp} max={100} variant="hp" side={side} />
}

/** 能量条（skew 液体） */
export function EnergyBar({ energy, max = 15, side }: { energy: number; max?: number; side: Side }) {
  return <LiquidBar value={energy} max={max} variant="energy" side={side} />
}

/** 大招 Q 键（液体波纹，能量满时发光） */
export function UltimateButton({ energy, max = 15 }: { energy: number; max?: number }) {
  const ready = energy >= max
  return (
    <div
      className="absolute left-4 top-24 z-50 flex items-center justify-center pointer-events-none transition-all duration-300"
      style={{
        width: "72px",
        height: "72px",
        filter: ready ? "drop-shadow(0 0 25px rgba(236,72,153,0.95))" : "drop-shadow(0 0 8px rgba(0,0,0,0.7))",
        scale: ready ? "1.15" : "1.0",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: "999px",
          border: "3px solid rgba(255,255,255,0.3)",
          backgroundColor: "rgba(0,0,0,0.85)",
          boxShadow: "inset 0 0 15px rgba(236,72,153,0.3)",
          backdropFilter: "blur(8px)",
        }}
      />
      <div style={{ position: "absolute", inset: "4px", overflow: "hidden", borderRadius: "999px" }}>
        <div
          className="wave-move-anim"
          style={{
            position: "absolute",
            left: "-50%",
            width: "200%",
            bottom: "-25%",
            height: "100%",
            backgroundImage: "linear-gradient(to top right, #f472b6, #60a5fa)",
            transform: `translateY(-${(energy / max) * 100}%)`,
            transition: "transform 0.3s ease-out, opacity 0.3s",
            opacity: ready ? "1" : "0.7",
            maskImage: WAVE_MASK,
            WebkitMaskImage: WAVE_MASK,
            maskRepeat: "repeat-x",
            WebkitMaskRepeat: "repeat-x",
          }}
        />
      </div>
      <span
        className="font-display absolute z-10 text-5xl font-black italic"
        style={{
          color: "#fff",
          transform: "translateY(1px)",
          filter: ready
            ? "drop-shadow(0 0 15px rgba(255,255,255,0.9))"
            : "drop-shadow(0 0 2px rgba(255,255,255,0.4))",
        }}
      >
        Q
      </span>
    </div>
  )
}

/** 玩家 HUD（昵称 + 状态标签 + 血条 + 能量条） */
export function PlayerHud({
  name,
  side,
  hp,
  energy,
  energyMax = 15,
  nameClassName = "",
}: {
  name: string
  side: Side
  hp: number
  energy: number
  energyMax?: number
  nameClassName?: string
}) {
  const isLeft = side === "left"
  const ready = energy >= energyMax
  return (
    <div
      className={[
        "pointer-events-none absolute z-40 flex w-[40vw] max-w-[450px] flex-col gap-2",
        isLeft ? "left-28 top-28" : "right-6 top-20 z-50 items-end",
      ].join(" ")}
    >
      <div
        className={["flex w-full items-end justify-between px-2", isLeft ? "" : "flex-row-reverse"].join(" ")}
        style={{ textShadow: "0 0 8px rgba(0,0,0,0.8)" }}
      >
        <span className={["font-display text-2xl font-black tracking-widest", nameClassName || "text-white"].join(" ")}>
          {name}
        </span>
        <span className="font-display text-sm font-bold tracking-widest text-yellow-400 drop-shadow-md">
          {ready ? "ULTIMATE READY [Q]" : "ENERGY"}
        </span>
      </div>
      <HpBar hp={hp} side={side} />
      <EnergyBar energy={energy} max={energyMax} side={side} />
    </div>
  )
}
