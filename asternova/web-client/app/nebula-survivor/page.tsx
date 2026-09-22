import type { Metadata, Viewport } from "next"
import { NebulaSurvivorPageClient } from "@/src/components/game-pages/NebulaSurvivorPageClient"

export const metadata: Metadata = {
  title: "星云求生",
  description: "星云之中生存到底",
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
}

export default function NebulaSurvivorPage() {
  return <NebulaSurvivorPageClient />
}
