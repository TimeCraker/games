"use client"

import * as React from "react"

/**
 * 虚拟摇杆：只在触摸设备渲染（桌面用键盘；旧版桌面也画摇杆是浪费屏幕）。
 * 交互完全走 pointer 事件，不做任何 transform 缩放容器（rules.md §15）。
 */
export function Joystick({ onChange, size = 118 }: { onChange: (x: number, y: number) => void; size?: number }) {
  const ref = React.useRef<HTMLDivElement>(null)
  const [knob, setKnob] = React.useState({ x: 0, y: 0 })
  const active = React.useRef(false)

  const handle = React.useCallback((e: React.PointerEvent) => {
    const el = ref.current
    if (!el) return
    const r = el.getBoundingClientRect()
    const cx = r.left + r.width / 2
    const cy = r.top + r.height / 2
    let dx = e.clientX - cx
    let dy = e.clientY - cy
    const max = r.width / 2 - 10
    const d = Math.hypot(dx, dy)
    if (d > max) { dx = (dx / d) * max; dy = (dy / d) * max }
    setKnob({ x: dx, y: dy })
    onChange(dx / max, dy / max)
  }, [onChange])

  return (
    <div
      ref={ref}
      className="pointer-events-auto relative touch-none rounded-full border border-white/12 bg-[radial-gradient(circle,rgba(216,163,60,0.06),rgba(5,6,7,0.30)_70%)] opacity-70"
      style={{ width: size, height: size }}
      onPointerDown={(e) => { active.current = true; (e.target as HTMLElement).setPointerCapture(e.pointerId); handle(e) }}
      onPointerMove={(e) => { if (active.current) handle(e) }}
      onPointerUp={() => { active.current = false; setKnob({ x: 0, y: 0 }); onChange(0, 0) }}
      onPointerCancel={() => { active.current = false; setKnob({ x: 0, y: 0 }); onChange(0, 0) }}
      aria-label="移动摇杆"
      role="application"
    >
      <div
        className="absolute left-1/2 top-1/2 rounded-full"
        style={{
          width: size * 0.44, height: size * 0.44,
          transform: `translate(calc(-50% + ${knob.x}px), calc(-50% + ${knob.y}px))`,
          background: "radial-gradient(circle at 38% 34%, #E9BE69, #A87C24 70%, #6B4A10)",
          boxShadow: "0 0 22px rgba(216,163,60,0.4), inset 0 1px 0 rgba(255,255,255,0.35)",
        }}
      />
    </div>
  )
}
