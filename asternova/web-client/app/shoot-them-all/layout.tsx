import type { ReactNode } from "react"

/**
 * 弹珠风暴是纵向 720×1280 竖屏游戏，自有 StaGameShell 做全视口等比缩放 + letterbox。
 *
 * 此前这里套的是 MobileLandscapeGameShell(designWidth=1180, designHeight=700) —— 那是
 * 横版舞台（星轨疾驰那类）的壳，会在移动端对本作再做一次横版缩放，竖屏下二次缩放
 * 叠 letterbox，375px 视口直接失真。本作不需要它，只保留 main 地标 + 安全区。
 */
export default function ShootThemAllLayout({ children }: { children: ReactNode }) {
  return (
    <main
      id="main-content"
      tabIndex={-1}
      className="relative min-h-[100dvh] w-full overflow-hidden bg-ink-1000"
    >
      {children}
    </main>
  )
}
