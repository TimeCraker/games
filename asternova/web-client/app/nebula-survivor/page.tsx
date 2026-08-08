import type { Viewport } from "next"
import { NebulaSurvivorPageClient } from "@/src/components/game-pages/NebulaSurvivorPageClient"

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
}

export default function NebulaSurvivorPage() {
  return <NebulaSurvivorPageClient />
}
