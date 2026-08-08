import type { ReactNode } from "react"
import { MobileLandscapeGameShell } from "@/src/components/game-shell/MobileLandscapeGameShell"

export default function ShootThemAllLayout({ children }: { children: ReactNode }) {
  return (
    <MobileLandscapeGameShell designWidth={1180} designHeight={700}>
      {children}
    </MobileLandscapeGameShell>
  )
}
