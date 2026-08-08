import type { Viewport } from "next"
import { MergePageClient } from "@/src/components/game-pages/MergePageClient"

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
}

export default function MergePage() {
  return <MergePageClient />
}
