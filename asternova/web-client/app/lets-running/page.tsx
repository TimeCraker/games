import type { Viewport } from "next"
import { LetsRunningPageClient } from "@/src/components/game-pages/LetsRunningPageClient"

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
}

export default function LetsRunningPage() {
  return <LetsRunningPageClient />
}
