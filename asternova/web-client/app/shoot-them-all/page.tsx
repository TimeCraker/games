import type { Metadata, Viewport } from "next"
import { ShootThemAllPageClient } from "@/src/components/game-pages/ShootThemAllPageClient"
import { ARCADE_BRAND, arcadeMetadataTitle } from "@/src/components/arcade/brand"

const brand = ARCADE_BRAND["shoot-them-all"]

export const metadata: Metadata = {
  title: arcadeMetadataTitle("shoot-them-all"),
  description: brand.tagline,
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
}

export default function ShootThemAllPage() {
  return <ShootThemAllPageClient />
}
