 "use client"

 import * as React from "react"

 type BluePurpleBlackholeProps = {
   className?: string
   intensity?: number
   interactive?: boolean
 }

 // ===== 新增代码 START =====
 // 蓝紫黑洞动效：倾斜 30° + 轻量鼠标跟随（用于主页与登录页背景复用）
 export function BluePurpleBlackhole(props: BluePurpleBlackholeProps) {
   const { className, intensity = 1, interactive = true } = props

   const wrapRef = React.useRef<HTMLDivElement | null>(null)
   const rafRef = React.useRef<number | null>(null)

   const targetRef = React.useRef({ x: 0, y: 0, d: 0 })
   const currentRef = React.useRef({ x: 0, y: 0, d: 0 })

   React.useEffect(() => {
     const el = wrapRef.current
     if (!el) return

     if (!interactive) {
       el.style.setProperty("--bh-x", "0px")
       el.style.setProperty("--bh-y", "0px")
       el.style.setProperty("--bh-r", "0deg")
       el.style.setProperty("--bh-tilt", "-30deg")
       el.style.setProperty("--bh-speed", "1")
       return
     }

     const onMove = (ev: PointerEvent) => {
       const rect = el.getBoundingClientRect()
       const cx = rect.left + rect.width / 2
       const cy = rect.top + rect.height / 2
       const dx = (ev.clientX - cx) / Math.max(1, rect.width)
       const dy = (ev.clientY - cy) / Math.max(1, rect.height)
       const d = Math.min(1, Math.sqrt(dx * dx + dy * dy))

       targetRef.current.x = dx
       targetRef.current.y = dy
       targetRef.current.d = d
     }

     window.addEventListener("pointermove", onMove, { passive: true })
     return () => {
       window.removeEventListener("pointermove", onMove)
     }
   }, [interactive])

   React.useEffect(() => {
     const el = wrapRef.current
     if (!el) return

     const tick = () => {
       const t = targetRef.current
       const c = currentRef.current

       c.x += (t.x - c.x) * 0.08
       c.y += (t.y - c.y) * 0.08
       c.d += (t.d - c.d) * 0.08

       const px = c.x * 26 * intensity
       const py = c.y * 22 * intensity
       const rot = c.x * 10 * intensity
       const tilt = -30 + c.y * 6 * intensity
       const speed = 1 + (1 - c.d) * 1.2 * intensity

       el.style.setProperty("--bh-x", `${px}px`)
       el.style.setProperty("--bh-y", `${py}px`)
       el.style.setProperty("--bh-r", `${rot}deg`)
       el.style.setProperty("--bh-tilt", `${tilt}deg`)
       el.style.setProperty("--bh-speed", `${speed}`)

       rafRef.current = window.requestAnimationFrame(tick)
     }

     rafRef.current = window.requestAnimationFrame(tick)
     return () => {
       if (rafRef.current) window.cancelAnimationFrame(rafRef.current)
       rafRef.current = null
     }
   }, [intensity])

   return (
     <div ref={wrapRef} className={["relative", className || ""].join(" ")}>
       <style>{`
         @keyframes bhSpin {
           0% { transform: translate(var(--bh-x), var(--bh-y)) rotate(var(--bh-tilt)) rotate(var(--bh-r)) rotate(0deg); }
           100% { transform: translate(var(--bh-x), var(--bh-y)) rotate(var(--bh-tilt)) rotate(var(--bh-r)) rotate(360deg); }
         }
         @keyframes bhBreathe {
           0%, 100% { transform: translate(var(--bh-x), var(--bh-y)) rotate(var(--bh-tilt)) rotate(var(--bh-r)) scale(1); opacity: .92; }
           50% { transform: translate(var(--bh-x), var(--bh-y)) rotate(var(--bh-tilt)) rotate(var(--bh-r)) scale(1.04); opacity: 1; }
         }
       `}</style>

       {/* 黑洞主体 */}
       <div className="pointer-events-none absolute left-1/2 top-[38%] h-[340px] w-[340px] -translate-x-1/2 -translate-y-1/2 sm:h-[420px] sm:w-[420px]">
         {/* 吸积盘 */}
         <div
           className="absolute left-1/2 top-1/2 h-[320px] w-[320px] -translate-x-1/2 -translate-y-1/2 rounded-full blur-[2px] sm:h-[400px] sm:w-[400px]"
           style={{
             background:
               "conic-gradient(from 210deg, rgba(99,102,241,0.05), rgba(56,189,248,0.55), rgba(168,85,247,0.78), rgba(99,102,241,0.62), rgba(56,189,248,0.55), rgba(99,102,241,0.05))",
             boxShadow:
               "0 0 24px rgba(56,189,248,0.20), 0 0 70px rgba(168,85,247,0.22), 0 0 120px rgba(99,102,241,0.18)",
             animation: "bhSpin calc(9s / var(--bh-speed)) linear infinite",
             transformOrigin: "center",
           }}
         />

         {/* 事件视界 */}
         <div
           className="absolute left-1/2 top-1/2 h-[178px] w-[178px] -translate-x-1/2 -translate-y-1/2 rounded-full sm:h-[220px] sm:w-[220px]"
           style={{
             background: "radial-gradient(circle at 45% 40%, rgba(0,0,0,0.98) 0 55%, rgba(0,0,0,0.0) 70%)",
             boxShadow: "0 0 42px rgba(0,0,0,1), inset 0 0 22px rgba(0,0,0,0.95)",
             animation: "bhBreathe 6.6s ease-in-out infinite",
           }}
         />

         {/* 微弱外晕 */}
         <div
           className="absolute left-1/2 top-1/2 h-[420px] w-[420px] -translate-x-1/2 -translate-y-1/2 rounded-full sm:h-[520px] sm:w-[520px]"
           style={{
             background:
               "radial-gradient(circle, rgba(56,189,248,0.08), rgba(168,85,247,0.06), rgba(0,0,0,0))",
             filter: "blur(1px)",
             opacity: 0.9,
           }}
         />
       </div>
     </div>
   )
 }
 // ===== 新增代码 END =====

