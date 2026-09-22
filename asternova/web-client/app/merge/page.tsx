import type { Metadata, Viewport } from "next"
import { MergePageClient } from "@/src/components/game-pages/MergePageClient"

export const metadata: Metadata = {
  title: "AsterNova Merge",
  description: "立体三消闯关",
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
}

export default function MergePage() {
  return <MergePageClient />
}
