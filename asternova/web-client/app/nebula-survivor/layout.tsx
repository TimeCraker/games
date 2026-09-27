import type { ReactNode } from "react"

/**
 * 星域突围**不使用** MobileLandscapeGameShell 的等比缩放壳。
 *
 * 实测取证（2026-09-27）：等比缩放壳会把整棵游戏子树按 min(vw/1366, vh/768) 缩放，
 * 真机竖屏 390×844 下 scale ≈ 0.2855 → 游戏被压成 390×210 条带、HUD 折合 4.6px。
 * 本作改为全屏自适应：画布填满视口，相机按任意纵横比自适应，HUD 用真实 CSS px。
 * 详见 docs/ui-polish/rules.md §15。
 */
export default function NebulaSurvivorLayout({ children }: { children: ReactNode }) {
  return (
    <main id="main-content" tabIndex={-1} className="relative h-dvh min-h-0 w-full overflow-hidden bg-space-black">
      {children}
    </main>
  )
}
