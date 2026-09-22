import type { Metadata, Viewport } from "next"
import { LetsRunningPageClient } from "@/src/components/game-pages/LetsRunningPageClient"

export const metadata: Metadata = {
  title: "星际酷跑",
  description: "奔跑躲避障碍的太空跑酷",
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
}

export default function LetsRunningPage() {
  return <LetsRunningPageClient />
}
