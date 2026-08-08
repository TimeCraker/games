import type { Viewport } from "next"
import { ShootThemAllPageClient } from "@/src/components/game-pages/ShootThemAllPageClient"

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
}

export default function ShootThemAllPage() {
  return <ShootThemAllPageClient />
}

