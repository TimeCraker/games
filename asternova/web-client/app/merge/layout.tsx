import type { ReactNode } from "react"
import { MobileLandscapeGameShell } from "@/src/components/game-shell/MobileLandscapeGameShell"

export default function MergeGameLayout({ children }: { children: ReactNode }) {
  return (
    <MobileLandscapeGameShell designWidth={1000} designHeight={1600}>
      {children}
    </MobileLandscapeGameShell>
  )
}
