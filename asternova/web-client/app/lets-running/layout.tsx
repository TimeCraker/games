import type { ReactNode } from "react"
import { MobileLandscapeGameShell } from "@/src/components/game-shell/MobileLandscapeGameShell"

export default function LetsRunningLayout({ children }: { children: ReactNode }) {
  return (
    <MobileLandscapeGameShell designWidth={1366} designHeight={768}>
      {children}
    </MobileLandscapeGameShell>
  )
}
